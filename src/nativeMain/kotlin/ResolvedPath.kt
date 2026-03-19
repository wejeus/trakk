import extension.compressHome
import okio.Path
import service.LinkLocation


// TODO check how these are really used...
enum class InclusionReason { EXPLICIT, FROM_DIR_MASK }


// virtual dirs/files do not exist locally, but refs in repository or dir matcher might

sealed class ResolvedPath(
    open val path: Path,
    open val location: LinkLocation
) {
    fun compress(os: OS): String {
        return when (location) {
            LinkLocation.HOME -> path.compressHome(os)
            LinkLocation.ROOT -> path.toString()
        }
    }

    final override fun hashCode(): Int {
        return path.hashCode()
    }

    final override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is ResolvedPath) return false
        return path == other.path
    }

    final override fun toString(): String {
        return if (DEBUG) {
            "$path (${this::class.simpleName},${location.toString().lowercase()})"
        } else {
            path.toString()
        }
    }
}

data class ActualFile(
    override val path: Path,
    val reason: InclusionReason,
    override val location: LinkLocation
): ResolvedPath(path, location), Actual

data class ActualDirectory(
    override val path: Path,
    override val location: LinkLocation
): ResolvedPath(path, location), Actual, Directory

// guaranteed absolute path by name only since local might not exist in FS
data class VirtualDirectory(
    override val path: Path,
    override val location: LinkLocation
): ResolvedPath(path, location), Virtual, Directory

// guaranteed absolute path by name only since local might not exist in FS
data class VirtualFile(
    override val path: Path,
    override val location: LinkLocation
): ResolvedPath(path, location), Virtual

// path will be resolved but file might not exist
data class VirtualFileOrDirectory(
    override val path: Path,
    override val location: LinkLocation
): ResolvedPath(path, location), Virtual

interface Actual {
    val path: Path
}

interface Virtual {
    val path: Path
}

interface Directory {
    val path: Path
}

class ResolutionBlock(
    val actualFiles: MutableSet<ActualFile> = mutableSetOf(),
    val actualDirs: MutableSet<ActualDirectory> = mutableSetOf(),
    val virtual: MutableSet<VirtualFileOrDirectory> = mutableSetOf()
)
