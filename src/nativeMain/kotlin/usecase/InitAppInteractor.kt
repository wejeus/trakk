package usecase

import service.AppConfigService
import service.INDEX_REPOSITORY_INDICATOR_FILENAME
import service.IndexService
import OS
import TILDE
import logDebug
import okio.FileSystem
import okio.Path
import okio.Path.Companion.toPath
import readBooleanInput
import readValidInputName


private enum class InitType { AS_NEW, FROM_EXISTING, FROM_EMPTY_DIR, INVALID_NOT_DIRECTORY, INVALID_NOT_EMPTY_OR_REPOSITORY }

class InitAppInteractor(
    private var os: OS,
    private var fs: FileSystem,
    private var appConfigService: AppConfigService,
    private var indexService: IndexService
) {

    // TODO: edge-case: a valid config file could exists but repository does not
    fun initAt(repositoryCandidatePath: String) {

        // 1. check presence and validity of potential preexisting config

        var forceOverwrite = false

        if (appConfigService.configFileExists()) {
            logDebug<InitAppInteractor>(appConfigService.ERROR_CONFIG_ALREADY_EXISTS)

            forceOverwrite = readBooleanInput("A config file already exists, continue and overwrite?")
            if (!forceOverwrite) {
                return
            }
        }

        // 2. check validity of proposed repository path

        val repositoryPath = if (repositoryCandidatePath.startsWith(TILDE)) {
            repositoryCandidatePath.replaceFirst(TILDE, os.home)
        } else {
            repositoryCandidatePath
        }.toPath(true)

        if (!repositoryPath.isAbsolute) {
            Log.info("Failure. Repository must be given as an absolute path or relative to user home")
            return
        }

        when (determineRepositoryInitProcessType(repositoryPath)) {
            InitType.AS_NEW,
            InitType.FROM_EXISTING,
            InitType.FROM_EMPTY_DIR -> {
                val profileName = readValidInputName("Specify a profile name for this machine")

                val config = appConfigService.createAndLoadNewConfig(repositoryPath, profileName, forceOverwrite)
                if (config != null) {
                    logDebug<InitAppInteractor>("create new config: success")
                    indexService.run {
                        initAtLocation(repositoryPath, profileName)
                        Log.info("Done. Repository initialized at: $repositoryPath for profile: $profileName")
                    }
                }
            }

            InitType.INVALID_NOT_DIRECTORY -> Log.info("Failure. Repository is not directory")
            InitType.INVALID_NOT_EMPTY_OR_REPOSITORY -> Log.info("Failure. Repository is not empty or a pre:existing trakk repository")
        }
    }

    private fun determineRepositoryInitProcessType(path: Path): InitType {
        if (fs.exists(path)) {
            if (!fs.metadata(path).isDirectory) {
                return InitType.INVALID_NOT_DIRECTORY
            }
            // must be a pre:existing directory and if so it must be either empty or existing trakk repository to use be used
            if (fs.exists(path.resolve(INDEX_REPOSITORY_INDICATOR_FILENAME))) {
                return InitType.FROM_EXISTING
            }

            return if (fs.list(path).isEmpty()) {
                InitType.FROM_EMPTY_DIR
            } else {
                InitType.INVALID_NOT_EMPTY_OR_REPOSITORY
            }
        } else {
            // repository path does not exist at all, init as completely new
            return InitType.AS_NEW
        }
    }
}