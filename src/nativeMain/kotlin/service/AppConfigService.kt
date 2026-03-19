package service

import OS
import extension.readJsonFile
import json
import kotlinx.serialization.Serializable
import logDebug
import logError
import logException
import okio.FileSystem
import okio.Path
import okio.Path.Companion.toPath


const val APP_CONFIG_FILENAME = ".trakk.config"

@Serializable
data class AppConfigSchema(
    val repository: String,
    val profile: String,
)

class AppConfigService(os: OS, private val fileSystem: FileSystem) {

    private var configPath: Path = os.home.toPath().resolve(APP_CONFIG_FILENAME)
    private var _config: AppConfigSchema? = null

    // if this is not null config file is guaranteed to exist and content points to valid resources/paths
    val config: AppConfigSchema?
        get() = _config

    val ERROR_CONFIG_ALREADY_EXISTS = "Config file already exists. Check: $configPath"

    fun createAndLoadNewConfig(repositoryPath: Path, profile: String, forced: Boolean = false): AppConfigSchema? {
        if (configFileExists() && !forced) {
            logError<AppConfigService>(ERROR_CONFIG_ALREADY_EXISTS)
            return null
        }
        return writeConfig(repositoryPath, profile, forced)
    }

    fun loadFromDisk(forced: Boolean = false): Boolean {
        if (_config != null && !forced) {
            return true
        }
        try {
            _config = readConfig()
            return true
        } catch (error: Exception) { // IOException, SerializationException
            logException<AppConfigService>(error)
        }
        return false
    }

    fun configFileExists(): Boolean {
        if (fileSystem.exists(configPath)) {
            return fileSystem.metadata(configPath).isRegularFile
        }
        return false
    }

    private fun readConfig(): AppConfigSchema? {
        logDebug<AppConfigService>("Reading configuration from: $configPath")
        return if (configFileExists()) {
            val config = fileSystem.readJsonFile<AppConfigSchema>(configPath)
            if (configValid(config)) {
                config
            } else {
                null
            }
        } else {
            logDebug<AppConfigService>("Could not read config file")
            null
        }
    }

    private fun configValid(config: AppConfigSchema?): Boolean {
        config?.let {
            if (fileSystem.exists(config.repository.toPath()) && config.profile.isNotEmpty()) {
                return true
            }
        }
        return false
    }

    fun writeConfig(repositoryPath: Path, profile: String, forced: Boolean): AppConfigSchema? {
        logDebug<AppConfigService>("Writing configuration to: $configPath")
        try {
            val data = AppConfigSchema(repositoryPath.toString(), profile)
            val encoded = json.encodeToString(data)

            // mustCreate sets fopen mode to "wx" where x indicate to fail if file exists
            fileSystem.write(configPath, !forced) {
                writeUtf8(encoded)
            }
            _config = data
            return _config
        } catch (err: Exception) {
            logException<AppConfigService>(err)
        }
        return null
    }
}
