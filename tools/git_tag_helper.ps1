<#
.SYNOPSIS
  Power-tag releases with semver and changelog summary.

.EXAMPLE
  ./tools/git_tag_helper.ps1 -Level patch -Push
#>
param(
  [ValidateSet("major","minor","patch")] [string]$Level = "patch",
  [switch]$PreRelease,
  [string]$PreId = "rc",
  [switch]$Push
)

function Get-CurrentTag {
  git describe --tags --abbrev=0 2>$null
}

function Bump-Version($v, $level, $pre, $preid) {
  if (-not $v) { return "0.1.0" }
  $parts = $v.TrimStart("v").Split(".")
  $major=[int]$parts[0]; $minor=[int]$parts[1]; $patch=[int]$parts[2]
  switch ($level) {
    "major" { $major++; $minor=0; $patch=0 }
    "minor" { $minor++; $patch=0 }
    "patch" { $patch++ }
  }
  $nv = "$major.$minor.$patch"
  if ($pre) { $nv = "$nv-$preid.1" }
  return $nv
}

$cur = Get-CurrentTag
$next = Bump-Version $cur $Level $PreRelease $PreId
$sha = git rev-parse HEAD
$range = if ($cur) { "$cur..$sha" } else { $sha }
$changelog = git log $range --pretty=format:"* %s (%h)" | Out-String

"Creating tag v$next"
git tag -a "v$next" -m "Release v$next`n`nChanges:`n$changelog"
if ($Push) {
  git push origin "v$next"
}
