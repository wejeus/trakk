package usecase

import service.LinkerService
import OS
import okio.FileSystem
import extension.sha256
import readChoiceInput
import service.AppConfigService

class SyncInteractor(
    private val fs: FileSystem,
    private val appConfigService: AppConfigService,
    private val linkerService: LinkerService,
    private val diffTask: DiffTask,
    private val brokenLinksTask: BrokenLinksTask
) {

    fun sync() {
        if (!appConfigService.loadFromDisk()) {
            return
        }

        val brokenLinks = brokenLinksTask.getBrokenLinks().sortedBy { it.type }
        if (brokenLinks.isEmpty()) {
            Log.info("Nothing to sync. All good.")
            return
        }

        linkerService.run {
            for (brokenRef in brokenLinks) {
                when (brokenRef) {
                    is BrokenLinkType.BothExistsWithINodeMismatch -> {
                        // Even though inode could be different for 2 files content could be same.
                        // We can then auto merge and it does not matter if we use mine or theirs as base
                        if (fs.sha256(brokenRef.local.toString()) == fs.sha256(brokenRef.ref.toString())) {
                            Log.info("(auto merge) relinking file [equivalent content]: ${brokenRef.local}")
                            link(brokenRef.local, brokenRef.ref, forced = true)
                        } else {
                            while (true) {
                                val answer = readChoiceInput(
                                    "Inode mismatch, pick which to use as new base for: ${brokenRef.local}",
                                    listOf("local", "ref", "show")
                                )
                                if (answer == "show") {
                                    diffTask.showDiff(brokenRef.local)
                                    continue
                                }
                                if (answer == "local") {
                                    link(brokenRef.local, brokenRef.ref, forced = true)
                                    break
                                } else {
                                    link(brokenRef.ref, brokenRef.local, forced = true)
                                    break
                                }
                            }
                        }
                    }
                    is BrokenLinkType.RefExistsLocalMissing -> {
                        val answer = readChoiceInput("Dangling ref: restore upstream file to local filesystem or remove ref? ${brokenRef.ref}", listOf("add", "remove"))
                        if (answer == "add") {
                            link(brokenRef.ref, brokenRef.local)
                        } else {
                            fs.delete(brokenRef.ref)
                        }
                    }
                    is BrokenLinkType.RefMissingLocalExists -> {
                        val answer = readChoiceInput("Untracked file: add to tracking? ${brokenRef.local}", listOf("add", "skip"))
                        if (answer == "add") {
                            link(brokenRef.local, brokenRef.ref)
                        }
                    }

                    is BrokenLinkType.WatchedDirDoesNotExistLocally -> Log.fatal("WatchedDirDoesNotExistLocally - not implemented yet!")
                }
            }
        }
    }
}