// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "igf",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .executableTarget(
            name: "igf"
        ),
        .testTarget(
            name: "igfTests",
            dependencies: ["igf"]
        ),
    ]
)
