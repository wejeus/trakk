import usecase.AddInteractor
import usecase.BrokenLinksTask
import usecase.InitAppInteractor
import usecase.ListInteractor
import usecase.RemoveInteractor
import usecase.ShowInteractor
import usecase.StatusInteractor
import usecase.SyncInteractor
import kotlinx.serialization.json.Json
import okio.FileSystem
import service.AppConfigService
import service.IndexService
import service.LinkerService
import usecase.DiffTask


// Lazy dependency injection
// As much as possible, to create valid objects at construction time, when not possible:
// ensure that the configuration of services is separated from their use.
class Injection {

    lateinit var os: OS
    lateinit var fileSystem: FileSystem

    lateinit var appConfigService: AppConfigService

    fun initialize(os: OS, fileSystem: FileSystem) {
        this.os = os
        this.fileSystem = fileSystem
        this.appConfigService = AppConfigService(os, fileSystem)
    }

    // Services

    // Use-case interactors should check config validity before using
    private val indexService: IndexService by lazy {
        IndexService(os, fileSystem, appConfigService)
     }

    private val linkerService: LinkerService by lazy {
        LinkerService(os, fileSystem, appConfigService)
    }

    // Interactors

    fun getInitAppInteractor(): InitAppInteractor {
        return InitAppInteractor(os, fileSystem, appConfigService, indexService)
    }

    fun getListInteractor(): ListInteractor {
        return ListInteractor(appConfigService, indexService)
    }

    fun getAddInteractor(): AddInteractor {
        return AddInteractor(os, fileSystem, appConfigService, indexService, linkerService)
    }

    fun getRemoveInteractor(): RemoveInteractor {
        return RemoveInteractor(os, fileSystem, appConfigService, indexService, linkerService)
    }

    fun getShowInteractor(): ShowInteractor {
        return ShowInteractor(appConfigService, getDiffTask(), getBrokenLinksTask())
    }

    fun getStatusInteractor(): StatusInteractor {
        return StatusInteractor(os, appConfigService, getBrokenLinksTask())
    }

    fun getSyncInteractor(): SyncInteractor {
        return SyncInteractor(fileSystem, appConfigService, linkerService, getDiffTask(), getBrokenLinksTask())
    }

    // Tasks

    fun getBrokenLinksTask(): BrokenLinksTask {
        return BrokenLinksTask(indexService, linkerService)
    }

    fun getDiffTask(): DiffTask {
        return DiffTask(os, fileSystem, indexService, linkerService)
    }

    companion object {
        private var _instance: Injection? = null

        fun instance(): Injection {
            if (_instance == null) {
                _instance = Injection()
            }
            return _instance!!
        }

        fun nuke() {
            _instance = null
        }
    }
}

val json = Json {
    prettyPrint = true
    ignoreUnknownKeys = true
}