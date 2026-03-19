import service.AppConfigService
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull

class ConfigTest {

    @Test
    fun `read and parse config works`() {
        val fakeEnvironment = initFakeEnvironment()

        val configService = AppConfigService(fakeEnvironment.os, fakeEnvironment.fs)
        val repository = fakeEnvironment.userHome.resolve("repository")
        val profile = "some_profile"
        configService.createAndLoadNewConfig(repository, profile)

        assertNotNull(configService.config)
        assertEquals(repository.toString(), configService.config?.repository)
        assertEquals(profile, configService.config?.profile)
    }
}