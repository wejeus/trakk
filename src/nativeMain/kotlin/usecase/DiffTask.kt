package usecase

import ActualDirectory
import ActualFile
import Ansi
import BrokenLinkType
import Log
import OS
import extension.readFileAsLines
import extension.resolvePath
import io.github.petertrr.diffutils.diff
import io.github.petertrr.diffutils.patch.DeltaType
import io.github.petertrr.diffutils.patch.Patch
import okio.FileSystem
import okio.Path
import service.IndexService
import service.LinkerService


class DiffTask(
    private val os: OS,
    private val fs: FileSystem,
    private val indexService: IndexService,
    private val linkerService: LinkerService
): Task {

    fun showDiff(path: Path) {
        when (val resolved = fs.resolvePath(os, path)) {
            is ActualDirectory -> {
                Log.info("Is directory - $path")
                return
            }

            is ActualFile -> {
                val found = indexService.findInMainIndex(resolved)
                found?.let {
                    val entry = linkerService.determineLinkStatus(found)
                    when (entry) {
                        is BrokenLinkType.BothExistsWithINodeMismatch -> {
                            val localContent = fs.readFileAsLines(found.local.path)
                            val refContent = fs.readFileAsLines(found.ref.path)

                            val out = diff(localContent, refContent)

                            Log.info(">>> ${found.local}", Ansi.Yellow)
                            Log.info("<<< ${found.ref}", Ansi.Yellow)

                            if (out.deltas.isNotEmpty()) {
                                out.printDiff()
                            } else {
                                Log.info("No diff, content is equivalent")
                            }
                        }

                        is BrokenLinkType.RefExistsLocalMissing -> {
                            Log.info("<<< ${found.ref}", Ansi.Yellow)
                            Log.info("Ref in index but not present in filesystem")
                        }

                        is BrokenLinkType.RefMissingLocalExists -> {
                            Log.info(">>> ${found.local}", Ansi.Yellow)
                            Log.info("File discovered by dir watcher, has not been staged for tracking")
                        }

                        else -> {
                            Log.info("Unknown extension.link type - $path")
                        }
                    }
                }
            }

            else -> {
                return
            }
        }
    }
}

fun Patch<String>.printDiff() {
    deltas.forEach {
        when (it.type) {
            DeltaType.CHANGE -> {
                Log.info("@@ ${it.source.position}~${it.target.position}")
                it.source.lines.forEach { line ->
                    Log.info(">$line", Ansi.Blue)
                }
                it.target.lines.forEach { line ->
                    Log.info("<$line", Ansi.Blue)
                }
            }

            DeltaType.DELETE -> {
                Log.info("@@ ${it.source.position},${it.source.lines.size}")
                it.source.lines.forEach { line ->
                    Log.info(">$line", Ansi.Red)
                }
            }

            DeltaType.INSERT -> {
                Log.info("@@ ${it.target.position},${it.target.lines.size}")
                it.target.lines.forEach { line ->
                    Log.info("<$line", Ansi.Green)
                }
            }

            DeltaType.EQUAL -> {}
        }
    }
}