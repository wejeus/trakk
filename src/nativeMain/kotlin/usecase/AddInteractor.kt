package usecase

import ActualFile
import service.AppConfigService
import service.IndexService
import service.LinkerService
import OS
import extension.listVerified
import okio.FileSystem
import extension.resolvePaths
import logDebug
import readBooleanInput
import service.UpdateKind


// Add local file (and local only) to index as a ref
class AddInteractor(
    private val os: OS,
    private val fs: FileSystem,
    private val appConfigService: AppConfigService,
    private val indexService: IndexService,
    private val linkerService: LinkerService
) {

    sealed interface Result {
        object InitFailure: Result
        class InvalidArgument(val reason: String): Result
        object Success: Result
    }

    // path(s) could be either a path to a file or directory (absolute, relative or ~ is ok).
    fun add(paths: List<String>, watch: Boolean, forced: Boolean = false): Result {
        if (!appConfigService.loadFromDisk()) { return Result.InitFailure }
        if (!indexService.loadFromDisk()) { return Result.InitFailure }

        if (watch && paths.size > 1) {
            return Result.InvalidArgument("--watch can only accept one directory at a time")
        }

        val resolved = fs.resolvePaths(os, paths)

        if (resolved.virtual.isNotEmpty()) {
            resolved.virtual.first {
                return Result.InvalidArgument("Invalid path \'${it.path}\' No such file or directory")
            }
        }

        logDebug<AddInteractor>("Adding resolved paths: $resolved")

        val acceptedDirs = resolved.actualDirs.filter {
            val ok = if (forced) {
                true
            } else {
                readBooleanInput("Recursively add all files in directory: ${it.path}?")
            }

            if (ok) {
                val files = fs.listVerified(it.path).map { file ->
                    ActualFile(file, InclusionReason.EXPLICIT, it.location)
                }
                resolved.actualFiles.addAll(files)
                true
            } else {
                false
            }
        }

        resolved.actualFiles.forEach {
            logDebug<AddInteractor>("Adding file: ${it.path}")
            // ref might already exist
            linkerService.link(it.path, indexService.asRefPath(it.path))
        }

        if (watch) {
            logDebug<AddInteractor>("Updating dir watcher with: ${acceptedDirs.size} entries")
            indexService.updateDirMatcher(acceptedDirs.map { Pair(it, UpdateKind.ADD) })
        }

        return Result.Success
    }
}