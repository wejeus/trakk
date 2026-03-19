// https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
// https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
enum class Ansi(val value: String) {
    RESET("\u001B[0m"),

    Red("\u001B[31m"),
    BrightRed("\u001B[91m"),
    Green("\u001B[32m"),
    Yellow("\u001B[33m"),
    Black("\u001B[30m"),
    Blue("\u001B[34m"),
    Magen("\u001B[35m"),
    Cyan("\u001B[36m"),
    White("\u001B[37m"),

    Default("\u001B[39m"),

    Bold("\u001B[;1;")
}

interface DeveloperLog {
    fun debug(sender: String?, message: String)
    fun error(sender: String?, message: String)
    fun exception(sender: String?, exception: Exception)
}

class DeveloperLogImpl: DeveloperLog {
    override fun debug(sender: String?, message: String) {
        if (DEBUG) {
            println("${Ansi.Cyan.value}<${sender}/debug> $message${Ansi.RESET.value}")
        }
    }

    override fun error(sender: String?, message: String) {
        if (ERROR) {
            println("${Ansi.Red.value}<${sender}/error> $message${Ansi.RESET.value}")
        }
    }

    override fun exception(sender: String?, exception: Exception) {
        if (ERROR) {
            println("${Ansi.BrightRed.value}<${sender}/exception> $exception${Ansi.RESET.value}")
        }
    }
}

val developerLog: DeveloperLog = DeveloperLogImpl()

inline fun <reified T> logDebug(message: String) {
    developerLog.debug(T::class.simpleName, message)
}

fun logDebug(message: String) {
    developerLog.debug(APP, message)
}

inline fun <reified T> logError(message: String) {
    developerLog.error(T::class.simpleName, message)
}

inline fun <reified T> logException(exception: Exception) {
    developerLog.exception(T::class.simpleName, exception)
}

// User intended
object Log {

    fun fatal(message: String?) {
        println("${Ansi.Red.value}fatal: $message${Ansi.RESET.value}")
    }

    fun info(message: String, color: Ansi = Ansi.Default) {
        println("${color.value}$message${Ansi.RESET.value}")
    }

    fun prompt(message: String, color: Ansi = Ansi.Default) {
        print("${color.value}$message${Ansi.RESET.value}")
    }
}
