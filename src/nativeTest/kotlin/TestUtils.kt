import extension.createEmptyFile
import extension.makeDirsIfNeeded
import okio.FileSystem
import okio.Path
import okio.Path.Companion.toPath
import okio.fakefilesystem.FakeFileSystem
import service.APP_CONFIG_FILENAME
import service.AppConfigSchema
import service.INDEX_PROFILES_ROOT_DIRNAME
import service.INDEX_PROFILE_CONFIG_FILENAME
import service.INDEX_REPOSITORY_INDICATOR_FILENAME

class FakeOS(private val fs: FileSystem, private val userHome: Path) : OS {
    // simplified only matches on filename so write tests accordingly with different filenames
    override fun inodeFor(path: Path): ULong? {
        return path.name.hashCode().toULong()
    }

    override fun link(source: String?, target: String?): Int {
        fs.write(target!!.toPath()) {  }
        return 0
    }

    override fun getEnvironment(key: String): String? {
        return "value"
    }

    override val home: String
        get() = userHome.toString()

    override val currentWorkingDir: String
        get() = home
}

data class FakeEnvironment(
    val userHome: Path,
    val os: OS,
    val fs: FileSystem,
    val repositoryDir: Path? = null,
    val profileName: String? = null,
    val profileDir: Path? = null,
    val profileConfigFile: Path? = null
)

// <creates>
// /Users
// /Users/fake_user
fun initFakeEnvironment(): FakeEnvironment {
    Injection.nuke()

    val userHome = "/Users/fake_user".toPath()
    val fakeFS = FakeFileSystem()
    val fakeOS = FakeOS(fakeFS, userHome)
    val fakeEnvironment = FakeEnvironment(
        userHome = userHome,
        os = fakeOS,
        fs = fakeFS,
    )

    fakeEnvironment.fs.makeDirsIfNeeded(userHome)
    Injection.instance().initialize(fakeOS, fakeFS)

    return fakeEnvironment
}

// <creates>
// /Users/fake_user/some_repository
// /Users/fake_user/some_repository/.trakk.repository
// /Users/fake_user/some_repository/profile/some_profile
// /Users/fake_user/some_repository/profile/some_profile/.trakk.profile.config
fun FakeEnvironment.createRepository(withProfile: String?): FakeEnvironment {
    val repository = userHome.resolve("some_repository")
    fs.makeDirsIfNeeded(repository)
    fs.createEmptyFile(repository.resolve(INDEX_REPOSITORY_INDICATOR_FILENAME))

    var profilePath: Path? = null
    var profileConfigFile: Path? = null
    withProfile?.let {
        profilePath = repository.resolve(INDEX_PROFILES_ROOT_DIRNAME).resolve(it)
        profileConfigFile = profilePath.resolve(INDEX_PROFILE_CONFIG_FILENAME)
        fs.makeDirsIfNeeded(profilePath)
        fs.createEmptyFile(profileConfigFile)
    }

    return this.copy(
        repositoryDir = repository,
        profileName = withProfile,
        profileDir = profilePath,
        profileConfigFile = profileConfigFile
    )
}

fun FakeEnvironment.initTrakk(): FakeEnvironment {
    fs.createEmptyFile(userHome.resolve(APP_CONFIG_FILENAME))

    val appConfig = AppConfigSchema(repository = repositoryDir.toString(), profile = profileName!!)
    fs.write(userHome.resolve(APP_CONFIG_FILENAME)) {
        writeUtf8(json.encodeToString(appConfig))
    }

    return this
}

fun FileSystem.allFiles(print: Boolean = false): Sequence<Path> {
    val result = listRecursively("/".toPath())
    result.forEach {
        if (print && !metadata(it).isDirectory) {
            println(it)
        }
    }
    return result
}
