package usecase

import Directory
import service.AppConfigService
import service.IndexService
import LINE_INDENT
import Virtual


class ListInteractor(
    private val appConfigService: AppConfigService,
    private val indexService: IndexService,
) {

    fun list() {
        if (!appConfigService.loadFromDisk()) {
            return
        }

        indexService.run {
            if (!loadFromDisk()) {
                return
            }

            val allRefs = mainRefs()
            if (allRefs.isNotEmpty()) {
                Log.info("Tracking files:")
                mainRefs()
                    .filter { it.local !is Directory }
                    .sortedBy { it.local.path }
                    .forEach {
                        Log.info("$LINE_INDENT${it.local}", Ansi.Yellow)
                    }
            }

            val dirMatchers = dirMatcherRefs()
            if (dirMatchers.isNotEmpty()) {
                Log.info("Watching dirs:")
                dirMatchers
                    .sortedBy { it.path }
                    .forEach {
                        val type = if (it is Virtual) " (virtual)" else ""
                        Log.info("$LINE_INDENT${it.path}$type", Ansi.Yellow)
                    }
            }
        }
    }
}