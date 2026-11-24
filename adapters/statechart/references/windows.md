# Windows runtime and commands

Use native PowerShell and Node with TypeScript stripping enabled (Node 22.18 or newer on the 22 line, or Node 23.6 or newer). Use a Java 11+ runtime compatible with TLC and prefer the tested combination of Node 24, Temurin 25, and TLC 1.7.4.

```powershell
$runner = Join-Path $statechartSkillDirectory 'scripts/statechart.ts'
node $runner $specPath --config $configPath --out $freshEvidencePath
$statechartExit = $LASTEXITCODE
```

Resolve those paths before running. The config defaults to the spec's sibling `.cfg`; optional `--view` takes a trusted local module. Use a new output directory for each invocation, including retries. Exit 0 means the configured check passed, 1 means TLC reported a violation, and 2 means the command could not complete. Inspect `report.md` for unchecked rules, bounds and partial drawing runs even when a report exists. Keep the original TLC output and any counterexample logs with the report. Do not infer a product bug or proof from the chart alone.

## Runtime lookup

On Windows the runner uses an absolute `TLA2TOOLS` override or `%LOCALAPPDATA%\Codex\statechart\tlc-1.7.4\tla2tools.jar`. It resolves Java from `JAVA`, the cached Temurin 25.0.5.1+2 JRE, `JAVA_HOME\bin\java.exe`, then `java` on PATH. Set overrides for the current PowerShell process only. Use an absolute path for each override because TLC runs in a scratch directory. The Windows runner does not install or fetch dependencies.

```powershell
$env:JAVA = 'C:\path with spaces\bin\java.exe'
$env:TLA2TOOLS = 'C:\path with spaces\tla2tools.jar'
& $env:JAVA -version
```

When provisioning the per-user cache, obtain the [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4) and verify SHA-256 `936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88`. For Windows x64, the tested [Temurin release](https://github.com/adoptium/temurin25-binaries/releases/tag/jdk-25.0.5.1%2B2) provides `OpenJDK25U-jre_x64_windows_hotspot_25.0.5.1_2.zip` with SHA-256 `3260a1b9899f30ac80d737daafc053042c525249f52d066101fbf81d78d73f25`. Extract its `jdk-25.0.5.1+2-jre` directory directly under the cache. Use a suitable installed runtime and overrides on other architectures. Preserve a repository's established tool version when checking its proof.
