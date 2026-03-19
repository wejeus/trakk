package usecase

import APP
import BrokenLinkType
import service.AppConfigService
import LINE_INDENT
import OS
import extension.compressHome


// Status indicate if there are sync issues that needs to be managed.
class StatusInteractor(
    private val os: OS,
    private val appConfigService: AppConfigService,
    private val brokenLinksTask: BrokenLinksTask
) {

    fun status() {
        if (!appConfigService.loadFromDisk()) {
            return
        }

        appConfigService.config?.let {
            val brokenLinks = brokenLinksTask.getBrokenLinks()

            if (brokenLinks.isNotEmpty()) {
                Log.info("Found broken or inconsistent links:")

                // group by type for easy print of segments
                val sortedLinks = brokenLinks.sortedBy { it.type }
                val printedHeadlines = mutableSetOf<String>()

                for (brokenLink in sortedLinks) {

                    if (brokenLink.type !in printedHeadlines) {
                        Log.info("\n${brokenLink.reason}")
                        printedHeadlines.add(brokenLink.type)
                    }

                    when (brokenLink) {
                        is BrokenLinkType.BothExistsWithINodeMismatch -> {
                            Log.info(
                                "$LINE_INDENT${brokenLink.local} != ${brokenLink.ref}",
                                Ansi.Yellow
                            )
                        }

                        is BrokenLinkType.RefExistsLocalMissing -> {
                            Log.info("$LINE_INDENT${brokenLink.ref}", Ansi.Yellow)
                        }

                        is BrokenLinkType.RefMissingLocalExists -> {
                            Log.info("$LINE_INDENT${brokenLink.local}", Ansi.Yellow)
                        }

                        is BrokenLinkType.WatchedDirDoesNotExistLocally -> {
                            Log.info("$LINE_INDENT${brokenLink.local.compressHome(os)}", Ansi.Yellow)
                        }
                    }
                }


            } else {
                Log.info("$APP - All OK")
            }
        }
    }
}