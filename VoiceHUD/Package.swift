// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "VoiceHUD",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        .package(url: "https://github.com/daltoniam/Starscream.git", from: "4.0.0")
    ],
    targets: [
        .executableTarget(
            name: "VoiceHUD",
            dependencies: ["Starscream"],
            path: "Sources/VoiceHUD"
        )
    ]
)
