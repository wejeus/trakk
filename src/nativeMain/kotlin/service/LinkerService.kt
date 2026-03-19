package service

import Actual
import ActualFile
import BrokenLinkType
import Directory
import OS
import Virtual
import VirtualFile
import extension.checkIsDescendantTo
import extension.checkIsNotDescendantTo
import extension.link
import extension.makeDirsIfNeeded
import logDebug
import logError
import okio.FileSystem
import okio.Path
import okio.Path.Companion.toPath

// Links must be hard links in order to harness the power of inodes!
class LinkerService(
    private val os: OS,
    private val fs: FileSystem,
    private val appConfigService: AppConfigService
) {

    fun link(source: Path, target: Path, forced: Boolean = false): Boolean {
        checkNotNull(appConfigService.config)
        source.checkIsNotDescendantTo(appConfigService.config!!.repository.toPath())
        target.checkIsDescendantTo(appConfigService.config!!.repository.toPath())

        logDebug<LinkerService>("Linking source: $source -> target: $target")

        if (!fs.exists(source)) {
            logError<LinkerService>("Link source does not exists: $source")
            return false
        }

        try {
            fs.makeDirsIfNeeded(target.parent ?: "/".toPath())

            if (forced) {
                fs.delete(target)
            }

            fs.link(os, source, target)
        } catch (err: Exception) {
            logError<LinkerService>("Linking failed, ${err.message}")
            return false
        }

        return true
    }

    // Only supports files. Link status of directories are not supported, ignore
    fun determineLinkStatus(link: Link): BrokenLinkType? {
        logDebug<LinkerService>("Link inodes: ${link.local} <${os.inodeFor(link.local.path)}> ${link.ref} <${os.inodeFor(link.ref.path)}>")

        if (link.local is Directory || link.ref is Directory) return null

        val (ref, local) = Pair(link.ref, link.local)

        if (link.local is Actual && link.ref is Actual) {
            if (os.inodeFor(local.path) != os.inodeFor(ref.path)) {
                return BrokenLinkType.BothExistsWithINodeMismatch(local.path, ref.path)
            }
        }

        if (link.local is Actual && link.ref is Virtual) {
            return BrokenLinkType.RefMissingLocalExists(link.local.path, link.ref.path)
        }

        if (link.local is Virtual && link.ref is Actual) {
            return BrokenLinkType.RefExistsLocalMissing(link.local.path, link.ref.path)
        }


        return null
    }

    // Unlinking is a basic removal of file.
    fun unlink(target: Path): Boolean {
        checkNotNull(appConfigService.config)
        target.checkIsDescendantTo(appConfigService.config!!.repository.toPath())

        logDebug<LinkerService>("Unlinking: $target")
        try {
            fs.delete(target)
        } catch (err: Exception) {
            logError<LinkerService>("Unlink failed, ${err.message}")
            return false
        }
        return true
    }

}
