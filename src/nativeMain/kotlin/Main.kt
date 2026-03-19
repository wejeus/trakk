import com.github.ajalt.clikt.core.main
import com.github.ajalt.clikt.core.subcommands
import okio.FileSystem



//            ┌────────────────┐
//            │    service.AppConfig   │
//            └────────────────┘
//
//   ┌────────────────┐  ┌────────────────┐
//   │  service.IndexService  │  │  service.LinkerService │
//   └────────────────┘  └────────────────┘
//
//             ┌────────────────┐
//             │  Interactors   │
//             └────────────────┘
//
//             ┌────────────────┐
//             │    Command     │
//             └────────────────┘
//
//             ┌────────────────┐
//             │     MainApp    │
//             └────────────────┘
//
fun main(args: Array<String>) {
    val os = Posix()
    val errorFlag = os.getEnvironment(ENVIRONMENT_VAR_ERROR)
    if (errorFlag != null && errorFlag == "true") {
        ERROR = true
    }
    val debugFlag = os.getEnvironment(ENVIRONMENT_VAR_DEBUG)
    if (debugFlag != null && debugFlag == "true") {
        DEBUG = true
    }

    Injection.instance().initialize(os, FileSystem.SYSTEM)

    TrakkCommand()
        .subcommands(
            ListCommand(),
            StatusCommand(),
            SyncCommand(),
            AddCommand(),
            RemoveCommand(),
            ShowCommand())
        .main(args)
}

// In general: follow unix philosophy - don't be chatty; only complain if something is broken/fails
// or ask for input if confirmation is needed. If a command succeeds don't print anything
// unless commands explicitly asks for output or situation demands it.

// Unix philosophy 2: when performing destructive actions such as removing a ref (tracked file) assume that the user
// know what he is doing and don't ask for confirmation to actually remove file.
// However, do ask for confirmation if command might have unintended side effects

// On error handling: in use-cases handle all reasonable expected situations but let core services
// handle remaining exceptional situations. Example: `remove` use-case manages checks for file existence
// but core service manages potential failures such as permission error on actual removal of file.
