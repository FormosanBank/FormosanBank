# Sourced by generate_xml.sh and validate.sh after they set
# repo_root. Sets formosanbank_path and defines dependency_status.
#
# Where FormosanBank is:
#   - FORMOSANBANK_PATH, if set;
#   - else ../.. when this corpus is the published copy (Corpora/<Name>/ inside
#     a FormosanBank checkout);
#   - else a sibling ../FormosanBank (the dev repo's layout).
if [[ -n "${FORMOSANBANK_PATH:-}" ]]; then
    formosanbank_path="$FORMOSANBANK_PATH"
elif [[ -f "$repo_root/../../QC/cleaning/clean_xml.py" ]]; then
    formosanbank_path="$repo_root/../.."
else
    formosanbank_path="$repo_root/../FormosanBank"
fi
formosanbank_path="$(cd "$formosanbank_path" && pwd -P)"

# The runs treat FormosanBank as read-only and compare its `git status` before
# and after. When this corpus lives inside that checkout, its own folder is the
# build's output, not the dependency, so it is left out of the comparison.
corpus_rel=""
case "$repo_root/" in
    "$formosanbank_path/"*) corpus_rel="${repo_root#"$formosanbank_path/"}" ;;
esac

dependency_status() {
    if [[ -n "$corpus_rel" ]]; then
        git -C "$formosanbank_path" status --porcelain -- . ":(exclude)$corpus_rel"
    else
        git -C "$formosanbank_path" status --porcelain
    fi
}
