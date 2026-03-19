package usecase

import DEBUG
import FakeEnvironment
import Injection
import allFiles
import createRepository
import extension.createEmptyFile
import extension.createFileAndDirs
import extension.readJsonFile
import initFakeEnvironment
import initTrakk
import okio.Path.Companion.toPath
import service.INDEX_ROOT_DIRNAME
import service.INDEX_HOME_DIRNAME
import service.ProfileConfigSchema
import kotlin.test.assertContains
import kotlin.test.Test
import kotlin.test.assertTrue

class AddInteractorTest {

    // fail fast on non-existing files or dirs

    // add a relative file/dir should always resolve to an absolute path and that absolute path should be stored (no relative paths should ever be allowed in index)

    fun setup(): FakeEnvironment {
        DEBUG = true
        return initFakeEnvironment()
            .createRepository("some_profile")
            .initTrakk()
    }

    @Test
    fun `add files adds link in repository`() {
        val env = setup()
        val interactor = Injection.instance().getAddInteractor()

        env.fs.createEmptyFile(env.userHome.resolve("file_in_home"))
        env.fs.createEmptyFile("/file_in_root".toPath())

        interactor.add(listOf("~/file_in_home", "/file_in_root"), watch = false)

        val result = env.fs.allFiles(false)
        assertContains(result, env.profileDir?.resolve(INDEX_HOME_DIRNAME)?.resolve("file_in_home"))
        assertContains(result, env.profileDir?.resolve(INDEX_ROOT_DIRNAME)?.resolve("file_in_root"))
    }

    @Test
    fun `add dirs walks and adds links for all files in repository`() {
        val env = setup()
        val interactor = Injection.instance().getAddInteractor()

        env.fs.createFileAndDirs(env.userHome.resolve("dir1/file_in_home_1"))
        env.fs.createFileAndDirs(env.userHome.resolve("dir1/file_in_home_2"))
        env.fs.createFileAndDirs("/dir2/file_in_root_1".toPath())
        env.fs.createFileAndDirs("/dir2/file_in_root_2".toPath())

        interactor.add(listOf("~/dir1", "/dir2"), watch = false, forced = true)

        env.profileDir?.let {
            val home = env.fs.listRecursively(it.resolve(INDEX_HOME_DIRNAME))
            assertContains(home, it.resolve(INDEX_HOME_DIRNAME).resolve("dir1/file_in_home_1"))
            assertContains(home, it.resolve(INDEX_HOME_DIRNAME).resolve("dir1/file_in_home_2"))

            val ext = env.fs.listRecursively(it.resolve(INDEX_ROOT_DIRNAME))
            assertContains(ext, it.resolve(INDEX_ROOT_DIRNAME).resolve("dir2/file_in_root_1"))
            assertContains(ext, it.resolve(INDEX_ROOT_DIRNAME).resolve("dir2/file_in_root_2"))
        }
    }

    @Test
    fun `add watched ROOT dir add files to repository and profile config`() {
        val env = setup()
        val interactor = Injection.instance().getAddInteractor()

        env.fs.createFileAndDirs("/dir1/file1".toPath())
        env.fs.createFileAndDirs("/dir1/file2".toPath())

        interactor.add(listOf("/dir1"), watch = true, forced = true)

        env.profileDir?.let {
            val dir = env.fs.listRecursively(it.resolve(INDEX_ROOT_DIRNAME))
            assertContains(dir, it.resolve(INDEX_ROOT_DIRNAME).resolve("dir1/file1"))
            assertContains(dir, it.resolve(INDEX_ROOT_DIRNAME).resolve("dir1/file2"))
        }
        val profileConfig = env.fs.readJsonFile<ProfileConfigSchema>(env.profileConfigFile!!)
        assertContains(profileConfig!!.dirs, "/dir1")
    }

    @Test
    fun `add watched HOME dir add files to repository and profile config`() {
        val env = setup()
        val interactor = Injection.instance().getAddInteractor()

        env.fs.createFileAndDirs(env.userHome.resolve("dir1/file1"))
        env.fs.createFileAndDirs(env.userHome.resolve("dir1/file2"))

        interactor.add(listOf("~/dir1"), watch = true, forced = true)

        env.profileDir?.let {
            val dir = env.fs.listRecursively(it.resolve(INDEX_HOME_DIRNAME))
            assertContains(dir, it.resolve(INDEX_HOME_DIRNAME).resolve("dir1/file1"))
            assertContains(dir, it.resolve(INDEX_HOME_DIRNAME).resolve("dir1/file2"))
        }
        val profileConfig = env.fs.readJsonFile<ProfileConfigSchema>(env.profileConfigFile!!)
        assertContains(profileConfig!!.dirs, "~/dir1")
    }

    @Test
    fun `adding more than 1 dir matcher at a time fails`() {
        setup()
        val interactor = Injection.instance().getAddInteractor()

        val result = interactor.add(listOf("~/dir1", "~/dir2"), watch = true, forced = true)

        assertTrue(result is AddInteractor.Result.InvalidArgument, "max 1 watched arg")
    }
}