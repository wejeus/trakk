package usecase

import BrokenLinkType
import Log
import okio.Path.Companion.toPath
import service.AppConfigService


class ShowInteractor(
    private val appConfigService: AppConfigService,
    private val diffTask: DiffTask,
    private val brokenLinksTask: BrokenLinksTask
) {

    fun show(path: String?) {
        if (!appConfigService.loadFromDisk()) {
            return
        }

        if (path == null) {
            val brokenItems = brokenLinksTask.getBrokenLinks()

            brokenItems.forEach { brokenRef ->
                when (brokenRef) {
                    is BrokenLinkType.BothExistsWithINodeMismatch -> {
                        diffTask.showDiff(brokenRef.ref)
                    }

                    is BrokenLinkType.RefExistsLocalMissing -> {
                        diffTask.showDiff(brokenRef.ref)
                    }

                    is BrokenLinkType.RefMissingLocalExists -> {
                        diffTask.showDiff(brokenRef.local)
                    }

                    is BrokenLinkType.WatchedDirDoesNotExistLocally -> {
                        Log.info("TODO $brokenRef")
                    }
                }

                // break between all items
                println()
            }
        } else {
            diffTask.showDiff(path.toPath())
        }
    }


}