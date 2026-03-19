package usecase

import ActualDirectory
import ActualFile
import service.IndexService
import service.LinkerService
import OS
import ResolvedPath
import VirtualDirectory
import VirtualFile
import VirtualFileOrDirectory
import extension.listVerified
import okio.FileSystem
import extension.resolvePaths
import logDebug
import okio.Path
import readBooleanInput
import service.AppConfigService
import service.LinkLocation
import service.UpdateKind


// Remove can only ever remove refs (or watched dir refs) from index
// path(s) could be either a path to a file or directory (absolute, relative or ~ is ok).
// side effect: when removing watched dir then also remove all refs originating from that dir (i.e. remove dir in index)
class RemoveInteractor(
    private val os: OS,
    private val fs: FileSystem,
    private val appConfigService: AppConfigService,
    private val indexService: IndexService,
    private val linkerService: LinkerService) {

    sealed interface Result {
        object InitFailure: Result
        object Success: Result
    }

    fun remove(paths: List<String>, forced: Boolean = false): Result {
        if (!appConfigService.loadFromDisk()) { return Result.InitFailure }
        if (!indexService.loadFromDisk()) { return Result.InitFailure }
        
        logDebug<RemoveInteractor>("Resolving paths: ${paths.joinToString(", ")}")
        val resolved = fs.resolvePaths(os, paths)

        val actualDirsToDelete = resolved.actualDirs.filter {
            val ok = checkTrackedAndConfirm(it, forced)

            if (ok) {
                resolved.actualFiles.addAll(readFilesFrom(it.path, it.location))
                true
            } else {
                false
            }
        }.toMutableSet()

        val virtualToDelete = resolved.virtual.mapNotNull {
            val ok = checkTrackedAndConfirm(it, forced)

            return@mapNotNull if (ok) {
                resolved.actualFiles.addAll(readFilesFrom(indexService.asRefPath(it.path), it.location))
                it
            } else {
                null
            }
        }.toMutableSet()

        // lastly add explicit files (no duplicates since storage is a Set)
        resolved.actualFiles.forEach {
            val ok = checkTrackedAndConfirm(it, forced)

            if (ok) {
                val ref = indexService.asRefPath(it.path)
                logDebug<RemoveInteractor>("Removing ref: $ref")
                linkerService.unlink(ref)
            }
        }

        // virtualToDelete can contain both virtual files/dirs, let indexService decide what to remove from watcher
        val deletable = actualDirsToDelete + virtualToDelete

        indexService.updateDirMatcher(deletable.map { Pair(it, UpdateKind.REMOVE) })

        deletable.forEach {
            val ref = indexService.asRefPath(it.path)
            logDebug<RemoveInteractor>("Removing ref: $ref")
            fs.deleteRecursively(ref)
        }

        return Result.Success
    }

    fun readFilesFrom(path: Path, location: LinkLocation): List<ActualFile> {
        return fs
            .listVerified(path)
            .map { file ->
                ActualFile(file, InclusionReason.FROM_DIR_MASK, location)
            }.toList()
    }

    fun checkTrackedAndConfirm(resolved: ResolvedPath, forced: Boolean): Boolean {
        return indexService.run {
            if (!isTracked(resolved)) {
                Log.fatal("Invalid path \'${resolved.path}\' File or directory not part of index or being tracked")
                return@run false
            }

            when (resolved) {
                is ActualDirectory,
                is VirtualDirectory,
                is VirtualFileOrDirectory -> {
                    if (forced) {
                        true
                    } else {
                        readBooleanInput("Stop tracking directory and recursively unstage all files? (${resolved.path})")
                    }
                }
                is ActualFile -> {
                    if (resolved.reason == InclusionReason.FROM_DIR_MASK || forced) {
                        true
                    } else {
                        readBooleanInput("Unlink file: ${resolved.path}?")
                    }
                }
                is VirtualFile -> TODO()
            }
        }
    }
}