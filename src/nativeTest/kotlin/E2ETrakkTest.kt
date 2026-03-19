//import Injection.configService
//import extension.createEmptyFile
//import extension.makeDirsIfNeeded
//import okio.Path.Companion.toPath
//import service.INDEX_HOME_DIRNAME
//import service.INDEX_PROFILES_CONTAINER_DIRNAME
//import kotlin.test.Test
//import kotlin.test.assertTrue
//
//class E2ETrakkTest {
//
//    // TODO structure dir1/dir2 - dir1 tracked and trying to remove dir2 should show warning that it is shadowed by dir1 mask and remove will be ignored
//
//    @Test
//    fun `command add files works`() {
//        val fakeEnv = initFakeEnvironment().createRepository("some_profile")
//        configService.createNewConfig(fakeEnv.repository!!, fakeEnv.profile!!)
//
//        // prepare fake fs
//        fakeEnv.fs.makeDirsIfNeeded(fakeEnv.userHome.resolve("sub_dir"))
//        fakeEnv.fs.makeDirsIfNeeded("/sub_dir".toPath())
//        val expected = listOf(
//            fakeEnv.userHome.resolve("file_in_home"),
//            fakeEnv.userHome.resolve("sub_dir/file_in_home2"),
//            "/file_in_root".toPath(),
//            "/sub_dir/file_in_root2".toPath()
//        )
//        expected.forEach {
//            fakeEnv.fs.createEmptyFile(it)
//        }
//
//        // when
//        val newFiles = listOf(
//            "~/file_in_home", "~/sub_dir/file_in_home2", "/file_in_root", "/sub_dir/file_in_root2",
//        )
//        Trakk.add(newFiles)
//
//        // then
//        val result = fakeEnv.fs.listRecursively("/".toPath())
//        expected.forEach {
//            assertTrue(result.contains(it), "unable to add file: $it")
//        }
//    }
//
//    @Test
//    fun `command add dir works`() {
//        val fakeEnv = initFakeEnvironment().createRepository("some_profile")
//        configService.createNewConfig(fakeEnv.repository!!, fakeEnv.profile!!)
//
//        // prepare fake fs
//        fakeEnv.fs.makeDirsIfNeeded("/sub_dir".toPath())
//        val expected = listOf(
//            "/sub_dir/file1".toPath(),
//            "/sub_dir/file2".toPath()
//        )
//        expected.forEach {
//            fakeEnv.fs.createEmptyFile(it)
//        }
//
//        // when
//        val newFiles = listOf("/sub_dir")
//        Trakk.add(newFiles, forced = true)
//
//        // then
//        val result = fakeEnv.fs.listRecursively("/".toPath())
//        expected.forEach {
//            assertTrue(result.contains(it), "unable to add file: $it")
//        }
//    }
//
//    @Test
//    fun `command remove files works`() {
//        val fakeEnv = initFakeEnvironment().createRepository("some_profile")
//        configService.createNewConfig(fakeEnv.repository!!, fakeEnv.profile!!)
//
//        // prepare fake fs
//
//        // local dirs
//        fakeEnv.fs.makeDirsIfNeeded(fakeEnv.userHome.resolve("sub_dir"))
//        fakeEnv.fs.makeDirsIfNeeded("/sub_dir".toPath())
//
//        // repo files
//        fakeEnv.fs.makeDirsIfNeeded(fakeEnv.repository.resolve(INDEX_PROFILES_CONTAINER_DIRNAME).resolve(fakeEnv.profile).resolve(
//            INDEX_HOME_DIRNAME
//        ).resolve("sub_dir"))
//        fakeEnv.fs.makeDirsIfNeeded(fakeEnv.repository.resolve(INDEX_PROFILES_CONTAINER_DIRNAME).resolve(fakeEnv.profile).resolve("sub_dir"))
//
//        val expected = listOf(
//            // local files
//            fakeEnv.userHome.resolve("file_in_home"),
//            fakeEnv.userHome.resolve("sub_dir/file_in_home2"),
//            "/file_in_root".toPath(),
//            "/sub_dir/file_in_root2".toPath(),
//
//            // repo files
//            fakeEnv.repository.resolve(INDEX_PROFILES_CONTAINER_DIRNAME).resolve(fakeEnv.profile).resolve(
//                INDEX_HOME_DIRNAME
//            ).resolve("file_in_home"),
//            fakeEnv.repository.resolve(INDEX_PROFILES_CONTAINER_DIRNAME).resolve(fakeEnv.profile).resolve(
//                INDEX_HOME_DIRNAME
//            ).resolve("sub_dir/file_in_home2"),
//            fakeEnv.repository.resolve(INDEX_PROFILES_CONTAINER_DIRNAME).resolve(fakeEnv.profile).resolve("/file_in_root"),
//            fakeEnv.repository.resolve(INDEX_PROFILES_CONTAINER_DIRNAME).resolve(fakeEnv.profile).resolve("/sub_dir/file_in_root2")
//        )
//
//        expected.forEach {
//            fakeEnv.fs.createEmptyFile(it)
//        }
//
//        // when
//        val filesToRemove = listOf(
//            "~/file_in_home", "~/sub_dir/file_in_home2", "/file_in_root", "/sub_dir/file_in_root2",
//        )
//        Trakk.remove(filesToRemove, forced = true)
//
//        // then
//        val result = fakeEnv.fs.listRecursively("/".toPath())
//
//        result.forEach { println(it) }
//
////        expected.forEach {
////            assertFalse(result.contains(it), "unable to add file: $it")
////        }
//    }
//
//    @Test
//    fun `command remove dir works`() {
//        val fakeEnv = initFakeEnvironment().createRepository("some_profile")
//        configService.createNewConfig(fakeEnv.repository!!, fakeEnv.profile!!)
//
//        // prepare fake fs
//        fakeEnv.fs.makeDirsIfNeeded("/sub_dir".toPath())
//        val expected = listOf(
//            "/sub_dir/file1".toPath(),
//            "/sub_dir/file2".toPath()
//        )
//        expected.forEach {
//            fakeEnv.fs.createEmptyFile(it)
//        }
//
//        // when
//        val newFiles = listOf("/sub_dir")
//        Trakk.add(newFiles, forced = true)
//
//        // then
//        val result = fakeEnv.fs.listRecursively("/".toPath())
//        expected.forEach {
//            assertTrue(result.contains(it), "unable to add file: $it")
//        }
//    }
//}