package usecase

import BrokenLinkType
import OS
import service.IndexService
import service.LinkerService


class BrokenLinksTask(
    private val indexService: IndexService,
    private val linkerService: LinkerService
): Task {

    fun getBrokenLinks(): List<BrokenLinkType> {
        val brokenLinks = mutableListOf<BrokenLinkType>()

        indexService.run {
            if (!loadFromDisk()) {
                return emptyList()
            }

            mainRefs().forEach { indexItem ->
                val entry = linkerService.determineLinkStatus(indexItem)
                if (entry != null) {
                    brokenLinks.add(entry)
                }
            }

            virtualDirMatcherRefs().forEach {
                val local = it.path
                brokenLinks.add(BrokenLinkType.WatchedDirDoesNotExistLocally(local, asRefPath(local)))
            }
        }

        return brokenLinks
    }
}