import kotlinx.cinterop.ByteVar
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.alloc
import kotlinx.cinterop.allocArray
import kotlinx.cinterop.convert
import kotlinx.cinterop.memScoped
import kotlinx.cinterop.pointed
import kotlinx.cinterop.ptr
import kotlinx.cinterop.toKString
import okio.Path
import platform.posix.PATH_MAX
import platform.posix.getcwd
import platform.posix.getenv
import platform.posix.getpwuid
import platform.posix.getuid
import platform.posix.perror
import platform.posix.stat


// Kotlin provides the POSIX platform library for all UNIX- and Windows-based targets, including Android and iOS. These platform libraries contain bindings to the platform's implementation, which follows the POSIX standard https://en.wikipedia.org/wiki/POSIX.
// Note: The platform.posix contents differ across platforms because of variations in POSIX implementations.
// https://en.wikipedia.org/wiki/C_POSIX_library
// https://kotlinlang.org/docs/native-c-interop.html
// https://github.com/JetBrains/kotlin/blob/master/kotlin-native/platformLibs/src/platform/osx/posix.def

interface OS {
    fun inodeFor(path: Path): ULong?
    fun link(source: String?, target: String?): Int
    fun getEnvironment(key: String): String?
    val home: String
    val currentWorkingDir: String
}

class Posix: OS {

    @OptIn(ExperimentalForeignApi::class)
    override fun getEnvironment(key: String): String? {
        memScoped {
            val value = getenv(key)
            return value?.toKString()
        }
    }

    @OptIn(ExperimentalForeignApi::class)
    override val home: String by lazy {
        memScoped {
            val home = getEnvironment("HOME")
            if (home != null) {
                home
            } else {
                val uid = getuid()
                getpwuid(uid)!!.pointed.pw_dir!!.toKString()
            }
        }
    }

    @OptIn(ExperimentalForeignApi::class)
    override val currentWorkingDir: String by lazy {
        memScoped {
            val bufferSize = PATH_MAX
            val buffer = allocArray<ByteVar>(bufferSize)
            // The getcwd() function may fail if:
            // Read or search permission was denied for a component of the pathname.  This is only checked in limited cases
            val result = getcwd(buffer, bufferSize.convert())
            if (result != null) {
                buffer.toKString()
            } else {
                ""
            }
        }
    }

    override fun link(source: String?, target: String?): Int {
        return platform.posix.link(source, target)
    }

    @OptIn(ExperimentalForeignApi::class)
    override fun inodeFor(path: Path): ULong? {
        memScoped {
            val statBuf = alloc<stat>()

            return if (stat(path.toString(), statBuf.ptr) == 0) {
                statBuf.st_ino
            } else {
                null
            }
        }
    }
}
