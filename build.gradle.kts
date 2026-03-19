import org.gradle.api.tasks.testing.logging.TestLogEvent

plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.kotlin.serialization)
}

kotlin {
    macosArm64() {
        binaries {
            executable {
                entryPoint = "main"
            }
        }
    }

    sourceSets {
        nativeMain.dependencies {
            implementation(libs.kotlinx.serialization.json)
            implementation(libs.kotlin.stdlib)
            implementation(libs.clikt)
            implementation(libs.multiplatform.diff)

            // kotlinx-io is probably better but still lacking some required things (like symlinks). Use Okio instead.
            // Follow kotlinx-io progress here:
            // https://github.com/Kotlin/kotlinx-io/issues/241
            // stabilization milestone: https://github.com/Kotlin/kotlinx-io/milestone/5
            // stabilization ticket: https://youtrack.jetbrains.com/projects/KT/issues/KT-71300/Stabilize-the-kotlinx-io-library
            implementation(libs.square.okio)
            implementation(libs.test.square.okio.fakefilesystem)
        }

        nativeTest.dependencies {
            implementation(libs.test.kotlin)
        }
    }
}

// Just running a Gradle "run" task fails since it expects input but STD in is null by default.
// https://github.com/gradle/gradle/issues/1251#issuecomment-459369978
tasks.named<Exec>("runDebugExecutableMacosArm64") {
    standardInput = System.`in`
}

// remove the .kexe extension of final binary
//tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinNativeLink>().configureEach {
//    doLast {
//        val output = outputFile.get()
//        val renamed = File(output.parent, output.nameWithoutExtension)
//        output.renameTo(renamed)
//    }
//}