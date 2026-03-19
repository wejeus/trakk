import okio.Path

/**
 * <mine> is what is located in your local fs, <theirs> refers to something located in <repository>
 */
sealed class BrokenLinkType(
    val type: String,
    val reason: String,
    val local: Path,
    val ref: Path
) {
    override fun toString(): String = "BrokenRef: local $local ref $ref"

    /**
     * Inode mismatch between local and ref
     */
    class BothExistsWithINodeMismatch(local: Path, ref: Path):
        BrokenLinkType("A", "Inode mismatch in link", local, ref)

    /**
     * Local file exists but is not present in index (discovered by trakked dir)
     */
    class RefMissingLocalExists(local: Path, ref: Path):
        BrokenLinkType("B", "Ref does not exist in repository but *is* present in local file system", local, ref)

    /**
     * New incoming (non-existing in system) upstream ref from index
     */
    class RefExistsLocalMissing(local: Path, ref: Path):
        BrokenLinkType("C", "Ref found in index that *is not* present in local file system", local, ref)


    class WatchedDirDoesNotExistLocally(local: Path, ref: Path):
        BrokenLinkType("D", "Watched dir not present in local file system", local, ref)
}
