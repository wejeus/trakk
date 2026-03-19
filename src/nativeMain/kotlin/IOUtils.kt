

fun readValidInputName(prompt: String): String {
    while(true) {
        print("${prompt.trim()}: ")
        val answer = readln().trim().replace(" ", "_")
        if (answer.isNotBlank()) {
            return answer
        }
    }
}

fun readBooleanInput(prompt: String): Boolean {
    while(true) {
        Log.prompt("${prompt.trim()} [y/n]: ")
        val answer = readln().trim()
        if (answer.isNotBlank() && (answer == "y" || answer == "n")) {
            return answer == "y"
        }
    }
}

fun readChoiceInput(prompt: String, choices: List<String>): String {
    val choicePrompt = choices.joinToString("/", "[", "]")
    while(true) {
        Log.prompt("${prompt.trim()} $choicePrompt: ")
        val answer = readln().trim()
        if (answer.isNotBlank() && choices.contains(answer)) {
            return answer
        }
    }
}
