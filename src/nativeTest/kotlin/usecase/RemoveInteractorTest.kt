package usecase

import DEBUG
import ERROR
import FakeEnvironment
import Injection
import createRepository
import extension.createFileAndDirs
import extension.readJsonFile
import initFakeEnvironment
import initTrakk
import json
import okio.Path
import okio.Path.Companion.toPath
import service.INDEX_ROOT_DIRNAME
import service.INDEX_HOME_DIRNAME
import service.ProfileConfigSchema
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class RemoveInteractorTest {

    fun setup(): FakeEnvironment {
        DEBUG = true
        ERROR = true
        return initFakeEnvironment()
            .createRepository("some_profile")
            .initTrakk()
    }

    @Test
    fun `remove files that exists locally but not in repository do not delete local files`() {
        val env = setup()

        val actualPaths: MutableList<Path> = mutableListOf()
        env.profileDir?.let {
            actualPaths.add(env.userHome.resolve("dir1/file_home"))
            actualPaths.add("/dir2/file_root".toPath())
            actualPaths.forEach {
              env.fs.createFileAndDirs(it)
            }
        }

        val params = listOf("~/dir1", "/dir2")
        val interactor = Injection.instance().getRemoveInteractor()
        interactor.remove(params, forced = true)

        assertTrue(
            env.fs.listRecursively("/".toPath()).toList().containsAll(actualPaths)
        )
    }

    @Test
    fun `remove tracked files that exists locally and in repository`() {
        val env = setup()

        env.profileDir?.let {
            env.fs.createFileAndDirs(env.userHome.resolve("dir1/file_home"))
            env.fs.createFileAndDirs("/dir2/file_root".toPath())
            env.fs.createFileAndDirs(it.resolve(INDEX_HOME_DIRNAME).resolve("dir1").resolve("file_home"))
            env.fs.createFileAndDirs(it.resolve(INDEX_ROOT_DIRNAME).resolve("dir2").resolve("file_root"))
        }

        val dirs = listOf("~/dir1", "/dir2")

        val interactor = Injection.instance().getRemoveInteractor()
        interactor.remove(dirs, forced = true)

        assertEquals(
            emptyList(),
            env.fs.listRecursively(env.profileDir!!.resolve(INDEX_HOME_DIRNAME)).toList()
        )
        assertEquals(
            emptyList(),
            env.fs.listRecursively(env.profileDir.resolve(INDEX_ROOT_DIRNAME)).toList()
        )
    }

    @Test
    fun `remove watched dir that does not exist in FS or repository`() {
        val env = setup()

        val dirs = listOf("~/nonexisting_dir_home", "/nonexisting_dir_root")
        val profileConfig = ProfileConfigSchema(dirs)
        env.fs.write(env.profileConfigFile!!) {
            writeUtf8(json.encodeToString(profileConfig))
        }

        val interactor = Injection.instance().getRemoveInteractor()
        interactor.remove(dirs, forced = true)

        val updatedProfileConfig = env.fs.readJsonFile<ProfileConfigSchema>(env.profileConfigFile)

        assertEquals(emptyList(), updatedProfileConfig!!.dirs)
    }

    @Test
    fun `remove watched dir that does not exist in FS - but dir has content in repository`() {
        val env = setup()

        env.profileDir?.let {
            env.fs.createFileAndDirs(it.resolve(INDEX_HOME_DIRNAME).resolve("dir1").resolve("file_home_1"))
            env.fs.createFileAndDirs(it.resolve(INDEX_ROOT_DIRNAME).resolve("dir2").resolve("file_root_1"))
        }

        val dirs = listOf("~/dir1", "/dir2")
        val profileConfig = ProfileConfigSchema(dirs)
        env.fs.write(env.profileConfigFile!!) {
            writeUtf8(json.encodeToString(profileConfig))
        }

        val interactor = Injection.instance().getRemoveInteractor()
        interactor.remove(dirs, forced = true)

        val updatedProfileConfig = env.fs.readJsonFile<ProfileConfigSchema>(env.profileConfigFile)

        assertEquals(emptyList(), updatedProfileConfig!!.dirs)
        assertEquals(
            emptyList(),
            env.fs.listRecursively(env.profileDir!!.resolve(INDEX_HOME_DIRNAME)).toList()
        )
        assertEquals(
            emptyList(),
            env.fs.listRecursively(env.profileDir.resolve(INDEX_ROOT_DIRNAME)).toList()
        )
    }
}