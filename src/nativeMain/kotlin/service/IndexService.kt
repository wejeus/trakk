package service

import ActualDirectory
import ActualFile
import ResolvedPath
import OS
import TILDE
import VirtualDirectory
import VirtualFile
import VirtualFileOrDirectory
import extension.createFileAndDirs
import extension.listVerified
import extension.readJsonFile
import extension.resolveDir
import extension.resolvePath
import extension.writeJsonFile
import kotlinx.serialization.Serializable
import logDebug
import logError
import logException
import okio.FileSystem
import okio.Path
import okio.Path.Companion.toPath

const val ERROR_INDEX_REPOSITORY_DOES_NOT_EXISTS = "Index does not exists"
const val ERROR_INDEX_PROFILE_DOES_NOT_EXISTS = "No profile set or exists in index"

const val INDEX_HOME_DIRNAME = "home"
const val INDEX_ROOT_DIRNAME = "root"
const val INDEX_PROFILES_ROOT_DIRNAME = "profiles"

const val INDEX_PROFILE_CONFIG_FILENAME = ".trakk.profile.config"
const val INDEX_REPOSITORY_INDICATOR_FILENAME = ".trakk.repository"

@Serializable
data class ProfileConfigSchema(
    val dirs: List<String> = emptyList(),
)

data class Link(val local: ResolvedPath, val ref: ResolvedPath)

enum class LinkLocation { HOME, ROOT }
enum class UpdateKind { ADD, REMOVE }

// Superset of tracked files (explicit + from watched dirs)
class MainIndex(
    val links: Set<Link>
)

// Set of files included from watched dirs
class DirMatcherIndex(
    val actualDirs: Set<ActualDirectory>,
    val virtualDirs: Set<VirtualDirectory>,
    val links: Set<Link>,
) {
    val allDirs: Set<ResolvedPath> = actualDirs + virtualDirs

    fun contains(resolved: ResolvedPath): Boolean {
        return allDirs.contains(resolved)
    }

    fun asPersistableEntries(os: OS): MutableSet<String> {
        return (actualDirs + virtualDirs).map { it.compress(os) }.toMutableSet()
    }
}


class IndexService(
    private val os: OS,
    private val fs: FileSystem,
    private val appConfigService: AppConfigService
) {

    // fileIndex holds all tracked files (including dirs) from both concrete files and files from dir matcher
    // When a dir matcher is parsed and do not contain any files, the dir matcher dir itself will not be added.
    // If a dir matcher do contain a file (from current FS or added earlier) both a dir + file will be added.
    //
    // Note: when reading files from repository all refs are guaranteed to exist (but locals might not)
    // dir watchers might add links for which locals exist but refs do not.
    private var mainIndex: MainIndex? = null
    private var dirMatcherIndex: DirMatcherIndex? = null

    fun initAtLocation(repositoryPath: Path, profileName: String) {
        logDebug<IndexService>("initialize new index at repository location: $repositoryPath")
        fs.createFileAndDirs(repositoryPath.resolve(INDEX_REPOSITORY_INDICATOR_FILENAME))

        if (profileExists(profileName)) {
            logDebug<IndexService>("profile (\"$profileName\") already exists, will not initialize new")
        } else {
            val profilePath = repositoryPath.resolve(INDEX_PROFILES_ROOT_DIRNAME).resolve(profileName)
            logDebug<IndexService>("creating new profile at: $profilePath")
            fs.createFileAndDirs(profilePath.resolve(INDEX_PROFILE_CONFIG_FILENAME))
        }
    }

    fun loadFromDisk(forced: Boolean = false): Boolean {
        if (mainIndex != null && !forced) {
            return true
        }
        if (!indexExists()) {
            logError<IndexService>(ERROR_INDEX_REPOSITORY_DOES_NOT_EXISTS)
            return false
        }
        if (!profileExists()) {
            logError<IndexService>(ERROR_INDEX_PROFILE_DOES_NOT_EXISTS)
            return false
        }

        try {
            mainIndex = readMainIndex()
            return true
        } catch (error: Exception) {
            // IOException, SerializationException
            logException<IndexService>(error)
        }
        return false
    }

    // for refs read from index local path might not exist since derived from watched dir
    // or link is broken due to local file has been removed. Also, a watched dir might not
    // exist locally.
    // If any locals do not exist recording should not fail, just continue to read what is possible.
    fun readMainIndex(): MainIndex {
        val links = mutableSetOf<Link>()

        links.addAll(readRefsFromDirectory(profileHomeDir, LinkLocation.HOME))
        links.addAll(readRefsFromDirectory(profileExtDir, LinkLocation.ROOT))

        val watched = readFromDirMatcher()
        dirMatcherIndex = watched
        links.addAll(watched.links)

        return MainIndex(links = links)
    }

    // A watched dir might not exist locally and a watched dir might contain subfolders.
    // Sub-dirs themselves should be ignored and only files returned (tracked or not)
    fun readFromDirMatcher(): DirMatcherIndex {
        logDebug<IndexService>("Reading profile extended configuration from: $profileConfigFile")

        val dirs = mutableSetOf<ActualDirectory>()
        val virtualDirs = mutableSetOf<VirtualDirectory>()
        val links = mutableSetOf<Link>()

        val profileConfig = fs.readJsonFile<ProfileConfigSchema>(profileConfigFile) ?: ProfileConfigSchema()

        profileConfig.let { config ->
            config.dirs.forEach { dir ->
                logDebug<IndexService>("Reading watched dir: $dir")

                when (val resolved = fs.resolveDir(os, dir.toPath())) {
                    is ActualDirectory -> {
                        links.addAll(readMatchedDir(resolved, resolved.location))
                        dirs.add(resolved)
                    }
                    is VirtualDirectory -> {
                        virtualDirs.add(resolved)
                    }
                    else -> {
                        logError<IndexService>("Unknown matcher directory: ${resolved.path}")
                    }
                }
            }
        }

        return DirMatcherIndex(
            actualDirs = dirs,
            virtualDirs = virtualDirs,
            links = links
        )
    }

    // Matched dir is always local (outside of repository), could be home or root. Both local and refs might not exist
    // (since watcher is just a wildcard for intended tracking)
    private fun readMatchedDir(directory: ActualDirectory, location: LinkLocation): Set<Link> {
        val links = mutableSetOf<Link>()
        fs.listRecursively(directory.path)
            .filter { path -> isValidFile(path) }
            .forEach {
                logDebug<IndexService>("Found watched file/directory: $it")
                val local = fs.resolvePath(os, it)
                val ref = fs.resolvePath(os,asRefPath(it))
                links.add(Link(local, ref))
            }

        return links
    }


    // Refs guaranteed to exist (since reading from actual dir) but locals might not (links might be broken)
    private fun readRefsFromDirectory(path: Path, location: LinkLocation): Sequence<Link> {
        logDebug<IndexService>("Reading directory: $path")

        return if (fs.exists(path)) {
            fs.listVerified(path).map {
                logDebug<IndexService>("Found ref: $it")
                val local = fs.resolvePath(os, refAsLocalPath(it, location))
                val ref = fs.resolvePath(os, it)
                Link(local, ref)
            }
        } else {
            emptySequence()
        }
    }

    fun isValidFile(path: Path): Boolean {
        var valid = false
        try {
            valid = fs.metadata(path).isRegularFile && path.name != ".DS_Store"
        } catch (_: Exception) {
            /* ignored */
        }
        logDebug<IndexService>("File consistency check: $path (valid: $valid)")
        return valid
    }

    // combination of all file refs in home/ext + files from watched dirs
    fun mainRefs(): Set<Link> {
        return mainIndex?.links ?: emptySet()
    }

    fun dirMatcherRefs(): Set<ResolvedPath> {
        return dirMatcherIndex?.allDirs ?: emptySet()
    }

    fun virtualDirMatcherRefs(): List<VirtualDirectory> {
        dirMatcherIndex?.let { watched ->
            return watched.virtualDirs.toList()
        }
        return emptyList()
    }

    fun findInMainIndex(resolved: ResolvedPath): Link? {
        return mainIndex?.links?.find { item ->
            item.local.path == resolved.path || item.ref.path == resolved.path
        }
    }

    fun isTracked(resolvedPath: ResolvedPath): Boolean {
        val tracked = when (resolvedPath) {
            is ActualDirectory,
            is VirtualDirectory,
            is VirtualFileOrDirectory-> {
                dirMatcherIndex?.contains(resolvedPath) == true
                        || findInMainIndex(resolvedPath) != null
            }
            is ActualFile, is VirtualFile -> {
                findInMainIndex(resolvedPath) != null
            }
        }

        logDebug<IndexService>("isTracked: ${resolvedPath.path} ($tracked)")
        return tracked
    }

    fun updateDirMatcher(directories: List<Pair<ResolvedPath, UpdateKind>>): Boolean {
        val matcherIndex = dirMatcherIndex
        check(matcherIndex != null) {
            logDebug<IndexService>("No previous matcher index loaded")
        }

        // Avoid storing user specific paths in config, compress user relative to ~
        val toUpdate = matcherIndex.asPersistableEntries(os)

        directories.forEach { (directory, kind) ->
            val compressedPath = directory.compress(os)
            when (kind) {
                UpdateKind.ADD -> toUpdate.add(compressedPath)
                UpdateKind.REMOVE -> toUpdate.remove(compressedPath)
            }
        }

        // TODO: add/remove might not cause any changes to config, possible to skip update
        val profileConfig = ProfileConfigSchema(dirs = toUpdate.toList())
        val ok = fs.writeJsonFile(profileConfigFile, profileConfig)

        if (!ok) {
            Log.fatal("Could not update profile config")
            return false
        }

        // since and update of watched dirs might change actual tracked files it is less complex to just reload entire index
        return loadFromDisk(forced = true)
    }

    // replace <profile_name>/<home>/some_file with <current_user_home_dir>/some_file
    // replace <profile_name>/<root>/some_file with /some_file
    // to not handle ~, it needs to be expanded before
    fun refAsLocalPath(ref: Path, refLocation: LinkLocation): Path {
        val childPath = ref.toString().substringAfter(profileRootDir.toString())

        return when (refLocation) {
            LinkLocation.HOME -> childPath.replace("/$INDEX_HOME_DIRNAME", os.home).toPath()
            LinkLocation.ROOT -> childPath.replace("/$INDEX_ROOT_DIRNAME", "").toPath()
        }
    }

    // always return abs path, if "~/asd" is wanted call for that explicitly on path.extension.expandhome - compressHome
    fun asRefPath(path: Path): Path {
        val ref = path.toString().run {
            if (startsWith(os.home)) {
                replaceFirst(os.home, profileHomeDir.toString()).toPath()
            } else {
                if (startsWith(Path.DIRECTORY_SEPARATOR)) {
                    profileExtDir.resolve(removePrefix(Path.DIRECTORY_SEPARATOR))
                } else {
                    profileExtDir.resolve(this)
                }
            }
        }

        logDebug<IndexService>("Transformed path: $path to ref: $ref")
        return ref
    }

    fun indexExists(): Boolean {
        appConfigService.config?.let {
            return fs.exists(it.repository.toPath())
        }
        return false
    }

    fun profileExists(profileName: String? = null): Boolean {
        appConfigService.config?.let {
            val name = profileName ?: it.profile
            val profilePath = it.repository.toPath().resolve(INDEX_PROFILES_ROOT_DIRNAME).resolve(name)
            return fs.exists(profilePath)
        }
        return false
    }

    fun prettyFormatItem(item: Link): String {
        val profileStripped = item.ref.toString().substringAfter(profileRootDir.toString())
        val formattedRef = if (profileStripped.startsWith("/${TILDE}")) {
            profileStripped.substringAfter("/")
        } else {
            profileStripped
        }

        return "(ref) $formattedRef -> (local) ${item.local}"
    }

    private val profileRootDir: Path by lazy {
        requireNotNull(appConfigService.config) { "service.AppConfig must not be null" }
            .run {
                repository.toPath()
                    .resolve(INDEX_PROFILES_ROOT_DIRNAME)
                    .resolve(profile)
            }
    }

    private val profileConfigFile: Path by lazy { profileRootDir.resolve(INDEX_PROFILE_CONFIG_FILENAME) }
    private val profileHomeDir: Path by lazy { profileRootDir.resolve(INDEX_HOME_DIRNAME) }
    private val profileExtDir: Path by lazy { profileRootDir.resolve(INDEX_ROOT_DIRNAME) }
}
