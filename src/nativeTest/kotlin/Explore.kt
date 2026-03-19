import extension.listVerified
import okio.FileSystem
import okio.Path.Companion.toPath
import service.LinkLocation
import kotlin.test.Ignore
import kotlin.test.Test
import kotlin.time.measureTime

class Explore {

    @Ignore
    @Test
    fun testFileWalk() {
        repeat(5) {
            val files = mutableSetOf<ResolvedPath>()
            val dirs = mutableSetOf<ResolvedPath>()

            val timeTaken = measureTime {
                val fs = FileSystem.SYSTEM
                fs.listVerified("/Users/wejeus/Movies".toPath()).forEach {
                    if (fs.metadata(it).isRegularFile) {
                        files.add(ActualFile(it, InclusionReason.EXPLICIT, LinkLocation.HOME))
                    }
                    if (fs.metadata(it).isDirectory) {
                        dirs.add(ActualFile(it, InclusionReason.EXPLICIT, LinkLocation.HOME))
                    }
                }
            }

            // Two if (check both regular or directory): Read: 7688 files, 3353 dirs in 949.101708ms
            // One if then else: Read: 7688 files, 3351 dirs in 1.072805250s
            println("Read: ${files.size} files, ${dirs.size} dirs in $timeTaken")
        }
    }
}