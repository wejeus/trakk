import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.arguments.argument
import com.github.ajalt.clikt.parameters.arguments.multiple
import com.github.ajalt.clikt.parameters.arguments.optional
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option
import usecase.AddInteractor
import kotlin.system.exitProcess


const val EXIT_SUCCESS = 0
const val EXIT_FAIL_INIT = 1
const val EXIT_FAIL_INVALID_ARGS = 2
const val EXIT_FAIL_EXECUTION = 3

private fun requireValidConfig() {
    if (!Injection.instance().appConfigService.configFileExists()) {
        Log.fatal(ERROR_MESSAGE_TRAKK_NOT_INITIALIZED)
        exitProcess(EXIT_FAIL_INIT)
    } else {
        logDebug("(pre:check) - valid config exists")
    }
}

const val ERROR_MESSAGE_TRAKK_NOT_INITIALIZED = "Trakk not initialized. Run: trakk --init <repository> (or -h for more help)"
const val ERROR_MESSAGE_INIT_FAILURE = "error during initialization"

class TrakkCommand : CliktCommand() {
    override val invokeWithoutSubcommand = true

    private val version by option("--version", help = "Show version").flag(default = false)
    private val init by option("--init", metavar = "repository path", help = "Create and init new repository at location <path>")
    private val profile by option("--profile", metavar = "name", help = "Switch active profile")

    override fun help(context: Context) = "Backup and tracking of files using inode linking (hard links)"

    override fun run() {
        if (version) {
            echo("$APP version $VERSION")
            exitProcess(0)  // TODO: check exit code
        }

        if (init != null) {
            val interactor = Injection.instance().getInitAppInteractor()
            interactor.initAt(init!!)
            exitProcess(0) // TODO: check exit code
        }

        if (profile != null) {
            Log.info("Switching profile $profile")
            exitProcess(0) // TODO: check exit code
        }

        val subcommand = currentContext.invokedSubcommand
        if (subcommand == null) {
            // invoked without a subcommand
            val configService = Injection.instance().appConfigService
            if (configService.configFileExists()) {
                if (configService.loadFromDisk()) {
                    configService.config?.let {
                        Log.info("Trakk is live in: ${it.repository}\nProfile: \"${it.profile}\"")
                    }
                }
            } else {
                Log.fatal(ERROR_MESSAGE_TRAKK_NOT_INITIALIZED)
            }
        }

        // flow control will pass to subcommand ...
    }
}

class ListCommand : CliktCommand(name = "list") {
    override fun help(context: Context) = "Print list of tracked files"
    override fun run() {
        requireValidConfig()
        val interactor = Injection.instance().getListInteractor()
        interactor.list()
    }
}

class AddCommand : CliktCommand(name = "add") {
    override val printHelpOnEmptyArgs = true
    private val watch by option("--watch", help = "Monitor directory for changes").flag(default = false)
    private val paths by argument("path").multiple(required = true)

    override fun help(context: Context) = "Add a file or directory to be included in tracking"
    override fun run() {
        requireValidConfig()
        val interactor = Injection.instance().getAddInteractor()
        when (val result = interactor.add(paths, watch)) {
            is AddInteractor.Result.InitFailure -> {
                Log.fatal(ERROR_MESSAGE_INIT_FAILURE)
                exitProcess(EXIT_FAIL_INIT)
            }
            is AddInteractor.Result.InvalidArgument -> {
                Log.fatal(result.reason)
                exitProcess(EXIT_FAIL_INVALID_ARGS)
            }
            is AddInteractor.Result.Success -> exitProcess(EXIT_SUCCESS)
        }
    }
}

class RemoveCommand : CliktCommand(name = "rm") {
    override val printHelpOnEmptyArgs = true
    private val paths by argument("path").multiple(required = true)

    override fun help(context: Context) = "Remove file or directory from being tracked"
    override fun run() {
        requireValidConfig()
        val interactor = Injection.instance().getRemoveInteractor()
        interactor.remove(paths)
    }
}

class ShowCommand : CliktCommand(name = "show") {
    private val path by argument("path").optional()

    override fun help(context: Context) = "Show diff for single file or leave empty to show all broken links"
    override fun run() {
        requireValidConfig()
        val interactor = Injection.instance().getShowInteractor()
        interactor.show(path)
    }
}

class StatusCommand : CliktCommand(name = "status") {
    override fun help(context: Context) = "Show any inconsistencies between original system files and indexed files/folders"
    override fun run() {
        requireValidConfig()
        val interactor = Injection.instance().getStatusInteractor()
        interactor.status()
    }
}

class SyncCommand : CliktCommand(name = "sync") {
    override fun help(context: Context) = "Synchronize potentially broken links and/or missing files"
    override fun run() {
        requireValidConfig()
        val interactor = Injection.instance().getSyncInteractor()
        interactor.sync()
    }
}