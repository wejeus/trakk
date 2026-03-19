import service.AppConfigSchema
import kotlin.test.Test

class IndexTest {


    // test: if allWatchedDirRefs contains both valid and invalid dirs

    @Test
    fun `ref and local path transformation works`() {
        val fakeEnv = initFakeEnvironment()

        val repository = fakeEnv.userHome.resolve("repository")
        val profileName = "some_profile"
        val someFileName = "somefile.txt"

        val config = AppConfigSchema(repository.toString(), profileName)

//        val indexService = IndexService(fakeEnv.os, fakeEnv.fs, config)

//        val localHomeExpanded = indexService.refAsLocalPath(
//            repository
//                .resolve("profile")
//                .resolve(profileName)
//                .resolve("~")
//                .resolve(someFileName),
//            resolveHome = true
//        )
//
//        val localSystem = indexService.refAsLocalPath(
//            repository
//                .resolve("profile")
//                .resolve(profileName)
//                .resolve(someFileName),
//        )
//
//        println(localSystem)
    }

    @Test
    fun `list correct index works`() {
//        val config = Config("", "")
//        val indexService = Module.indexService(config)
//        println("home:")
//        indexService?.run {
//            index.home.map {
//                println(prettyFormatItem(it))
//            }
//        }
//        println("root:")
//        indexService?.run {
//            index.root.map {
//                println(prettyFormatItem(it))
//            }
//        }
    }
}