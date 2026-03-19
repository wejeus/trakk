package extension

import ActualDirectory
import ActualFile
import ResolvedPath
import OS
import ResolutionBlock
import TILDE
import VirtualDirectory
import VirtualFile
import VirtualFileOrDirectory
import errnoToIOException
import json
import logDebug
import logError
import logException
import okio.Buffer
import okio.FileSystem
import okio.HashingSource
import okio.IOException
import okio.Path
import okio.Path.Companion.toPath
import okio.buffer
import okio.use
import platform.posix.errno
import service.LinkLocation


// Path
// -------------------------------------------------------------------------------------------------
// Note for path: Path does not automatically expand "~".

fun Path.isHomeRelative(os: OS): Boolean {
    return toString().startsWith(TILDE) || toString().startsWith(os.home)
}

fun Path.expandShellHomeIndicatorIfNeeded(os: OS): Path {
    return applyIf(toString().startsWith(TILDE)) {
        toString().replaceFirst(TILDE, os.home).toPath()
    }
}

fun Path.compressHome(os: OS): String {
    return this.toString().replaceFirst(os.home, TILDE)
}

fun Path.checkIsDescendantTo(path: Path) {
    if (!toString().startsWith(path.toString())) {
        throw IllegalStateException("Path descendant check failed")
    }
}

fun Path.checkIsNotDescendantTo(path: Path) {
    if (toString().startsWith(path.toString())) {
        throw IllegalStateException("Path descendant check failed")
    }
}


// FileSystem
// -------------------------------------------------------------------------------------------------


fun FileSystem.createEmptyFile(path: Path) {
    require(path.isAbsolute)
    write(path) { /* write empty marker file */ }
}

fun FileSystem.makeDirsIfNeeded(path: Path) {
    require(path.isAbsolute)
    createDirectories(path)
}

fun FileSystem.createFileAndDirs(path: Path) {
    require(path.isAbsolute)
    path.parent?.let {
        makeDirsIfNeeded(it)
    }
    createEmptyFile(path)
}

fun FileSystem.listVerified(path: Path): Sequence<Path> {
    if (!exists(path)) {
        return emptySequence()
    }
    return listRecursively(path, followSymlinks = false)
        .filter { it.name != ".DS_Store" }
}

// Expands and resolves to absolute paths. If resolved file/directory is guarnateed to exists.
// Unresolved files are ignored.
fun FileSystem.resolvePaths(os: OS, paths: List<String>): ResolutionBlock {
    val resolved = ResolutionBlock()
    paths
        .map { resolvePath(os, it.toPath()) }
        .forEach {
            when (it) {
                is ActualDirectory -> resolved.actualDirs.add(it)
                is ActualFile -> resolved.actualFiles.add(it)
                is VirtualFileOrDirectory -> resolved.virtual.add(it)
                // TODO het virtual dir or file dont know how to determine whcih from params
                else -> {
                    logError<FileSystem>("Could not resolve file/directory ${it.path}")
                }
            }
        }

    return resolved
}

fun FileSystem.resolveDir(os: OS, unresolved: Path): ResolvedPath {
    val expanded = unresolved
        .normalized()
        .expandShellHomeIndicatorIfNeeded(os).let {
            if (it.isRelative) {
                os.currentWorkingDir.toPath().resolve(it)
            } else {
                it
            }
        }

    // should now have /file or /User/wejeus/file or /cwd/file
    val location = if (expanded.isHomeRelative(os)) LinkLocation.HOME else LinkLocation.ROOT

    try {
        if (metadata(expanded).isDirectory) {
            return ActualDirectory(expanded, location)
        }
    } catch (_: Exception) {
        logDebug<FileSystem>("Could not read directory metadata. Most likely directory does not exists locally: $expanded")
    }

    return VirtualDirectory(expanded, location)
}

// resolving ../../ handled as prestep through normalize
// first expand ~ since it is shell specific (raw input)
// second try to determine if real file otherwise virual path
// what about symlinks?
fun FileSystem.resolvePath(os: OS, unresolved: Path): ResolvedPath {
    val expanded = unresolved
        .normalized()
        .expandShellHomeIndicatorIfNeeded(os).let {
            if (it.isRelative) {
                os.currentWorkingDir.toPath().resolve(it)
            } else {
                it
            }
        }

    // should now have /file or /User/wejeus/file or /cwd/file
    val location = if (expanded.isHomeRelative(os)) LinkLocation.HOME else LinkLocation.ROOT

    try {
        if (metadata(expanded).isDirectory) {
            return ActualDirectory(expanded, location)
        }
        if (metadata(expanded).isRegularFile) {
            return ActualFile(expanded, InclusionReason.EXPLICIT, location)
        }
    } catch (_: Exception) {}

    logDebug<FileSystem>("Could not read file metadata. Most likely file does not exists locally $expanded")
    return VirtualFileOrDirectory(expanded, location)
}

fun FileSystem.readFile(path: Path): String {
    source(path).use { fileSource ->
        return fileSource.buffer().readUtf8()
    }
}

fun FileSystem.readFileAsLines(path: Path): List<String> {
    val lines = mutableListOf<String>()
    source(path).buffer().use { source ->
        while (true) {
            val line = source.readUtf8Line() ?: break
            lines.add(line)
        }
    }
    return lines
}

inline fun <reified T> FileSystem.readJsonFile(path: Path): T? {
    try {
        if (!exists(path)) {
            logDebug<FileSystem>("File does not exists: $path")
            return null
        }
        if (!metadata(path).isRegularFile) {
            logDebug<FileSystem>("File is not a regular file: $path")
            return null
        }
        val content = readFile(path)
        if (content.isBlank()) {
            logDebug<FileSystem>("File empty: $path")
            return null
        }
        return json.decodeFromString<T>(content)
    } catch (err: Exception) {
        logException<FileSystem>(err)
        return null
    }
}

inline fun <reified T> FileSystem.writeJsonFile(path: Path, content: T): Boolean {
    try {
        logDebug<FileSystem>("Writing json to: $path")
        val data = json.encodeToString(content)
        logDebug<FileSystem>("Data: $data")
        write(path) {
            writeUtf8(data)
        }
        return true
    } catch (err: Exception) {
        logException<FileSystem>(err)
    }
    return false
}

// fail if target already exists, should have been prevented or handled by upstream
fun FileSystem.link(os: OS, source: Path, target: Path) {
    if (exists(target)) {
        throw IOException("Already exists: $target")
    }

    val result = os.link(source.toString(), target.toString())
    if (result != 0) {
        throw errnoToIOException(errno)
    }
}

fun FileSystem.sha256(path: String): String {
    val filePath = path.toPath()

    source(filePath).use { fileSource ->
        val hashingSource = HashingSource.sha256(fileSource)

        val buffer = Buffer()
        while (hashingSource.read(buffer, 8192) != -1L) {
            buffer.clear() // discard data, we only need the hash
        }

        val hash = hashingSource.hash
        return hash.hex()
    }
}
