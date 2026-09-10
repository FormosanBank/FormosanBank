Wrote /tmp/claude-1000/-workspace-FormosanBank/f7c21112-7392-4bac-8bf9-f97b2753559c/scratchpad/wt-mtier/QC/validation/RULES.md (91 rules)
— add the rule
to its module's `RULES` list and regenerate.

**HARD** fails the run (exit 1 unless `--no-exit-on-hard`); **SOFT** and
**WARN** are reported and do not. Scope `corpus` means the rule needs the
whole collection, not one file. Per-finding detail goes to the findings CSV
the validator names on its `Details:` line, never to the terminal.

> **Duplicate rule ids.** These ids are claimed by more than one
> rule, so a finding under one is ambiguous until they are
> renumbered:

> - **V070** — `validate_glosses.py:gloss_code_as_FORM`; `validate_xml.py:phon_placement`

## `validate_xml.py` — XSD conformance and structure

| Rule | Mnemonic | Severity | Scope | Checks |
| --- | --- | --- | --- | --- |
| V000 | `schema_validation` | HARD | file | Validate the parsed tree against the canonical XSD. |
| V001 | `root_must_be_TEXT` | HARD | file | The document root element must be TEXT. |
| V010 | `count_s_without_form` | SOFT | file | count S elements that have no FORM children. |
| V011 | `W_must_have_FORM` | HARD | file | every <W> element must have at least one FORM child. |
| V012 | `M_must_have_FORM` | HARD | file | every <M> element must have at least one FORM child. |
| V013 | `S_must_have_original_FORM` | HARD | file | every S that HAS at least one FORM must have one with kindOf='original'. |
| V014 | `count_missing_standard_form` | SOFT | file | count S/W/M elements that have FORM children but none with kindOf='standard'. |
| V015 | `S_at_most_one_original_FORM` | HARD | file | each S must have at most one direct-child *base* FORM kindOf='original'. |
| V017 | `form_must_have_content` | HARD | file | every <FORM> element must have non-empty text content. |
| V022 | `M_originals_distinct_lang` | HARD | file | on an M element, multiple TRANSL kindOf='original' must have distinct xml:lang. |
| V023 | `transl_must_have_xml_lang` | HARD | file | every TRANSL element must have an xml:lang attribute. |
| V026 | `M_transl_kindof_enum` | HARD | file | TRANSL/@kindOf at M level must be 'original' or 'standard' when set. |
| V035 | `xml_lang_is_iso_639_3` | HARD | file | Every xml:lang attribute on every element must be a valid ISO 639-3 code, or in the explicit allow-list of non-ISO tags FormosanBank accepts. |
| V036 | `text_dialect_valid` | HARD | file | TEXT/@dialect is required and must be valid for the language. |
| V039 | `id_unique_within_file` | HARD | file | id values must be unique across S, W, M within a single file. |
| V051 | `audio_empty_file` | HARD | file | AUDIO/@file, if present, must be non-empty. |
| V052 | `audio_single_file_mode_requires_start_end` | HARD | file | AUDIO start/end attributes: required only when the AUDIO element has no @file of its own (single-file mode). |
| V053 | `orphan_audio` | HARD | file | AUDIO with no @file when TEXT/@audio is also absent is an orphan. |
| V054 | `audio_end_after_start` | HARD | file | Each <AUDIO> element with numeric start/end must have start < end. |
| V070 | `phon_placement` | HARD | file | PHON is only permitted as a child of S, W, or M. |
| V071 | `phon_kindof_enum` | HARD | file | PHON/@kindOf must be 'original' or 'standard' when set. |
| V072 | `duplicate_phon_kindof` | HARD | file | at most one PHON per kindOf value per parent element (S, W, M). |
| V073 | `phon_non_empty` | HARD | file | PHON must have non-empty text content. |
| V081 | `text_id_unique_across_published_corpora` | HARD | corpus | a TEXT/@id in the corpus-under-test must not collide with any TEXT/@id in published Corpora/. Cross-file rule; consults the CorpusIndex's published_ids. |
| V084 | `transl_ver_value_in_allowlist` | HARD | file | when TRANSL/@ver is set, its value must be in the project allowlist. |
| V085 | `multi_same_lang_transl_requires_ver` | HARD | file | when a parent has multiple TRANSL children sharing the same xml:lang, at least one must carry a `ver` attribute to discriminate them. |
| V145 | `degenerate_all_single_M_tier` | SOFT | file | M level present but the file carries no parsing. |
| V148 | `W_less_S_in_segmented_file` | SOFT | file | a partially word-segmented file. |
| V149 | `alternate_FORM_requires_base_sibling` | HARD | file | a variant FORM must have exactly one base FORM in its own tier. |
| V150 | `alternate_FORM_low_overlap` | SOFT | file | an alternate FORM that does not look like a spelling variant of its sibling. |
| V151 | `S_TRANSL_has_no_kindOf` | SOFT | file | an S-level TRANSL must not carry @kindOf. |
| V152 | `mirrored_M_tier` | SOFT | file | an M that merely mirrors its parent W. |
| V156 | `form_ver_value_in_allowlist` | HARD | file | when FORM/@ver is set, its value must be in the project allowlist. |
| V157 | `legacy_alternate_kindOf` | SOFT | file | FORM[@kindOf='alternate'] is the deprecated variant spelling. |

## `validate_text.py` — text and typography

| Rule | Mnemonic | Severity | Scope | Checks |
| --- | --- | --- | --- | --- |
| V110 | `smart_quotes` | SOFT | file | smart quotes in S-level standard FORM. |
| V111 | `imbalanced_parens` | SOFT | file | imbalanced ASCII parentheses in S-level standard FORM. |
| V112 | `repeated_punct` | SOFT | file | repeated terminal punctuation (??, !!) in S-standard FORM. |
| V113 | `consecutive_dashes` | SOFT | file | two or more consecutive dashes in S-standard FORM. |
| V114 | `multiple_whitespace` | SOFT | file | two or more consecutive spaces in S-standard FORM. |
| V115 | `mismatched_quotes` | SOFT | file | left/right smart quotes do not balance in S-standard FORM. |
| V116 | `non_ascii_in_form` | SOFT | file | count non-ASCII characters in ALL FORM tiers. |
| V120 | `null_in_S_standard` | SOFT | file | null symbol '∅' in S-level standard FORM is a warning. |
| V121 | `parens_slashes_in_W_or_M_FORM` | HARD | file | parens or '/' in W- or M-level FORM is forbidden. |
| V122 | `parens_slashes_anywhere` | SOFT | file | parens or '/' anywhere in FORM or TRANSL. |
| V123 | `null_in_WM_std_requires_sister_original_null` | HARD | file | if a W- or M-level standard FORM contains the null symbol, the W's or M's direct-child kindOf='original' FORM must also contain it. |
| V124 | `null_in_M_requires_parent_W_and_S_original` | HARD | file | if an M FORM contains '∅', the parent W must also have a FORM containing '∅', AND the S-level original-tier FORM must also contain '∅'. |
| V125 | `null_in_W_requires_child_M_and_S_original` | HARD | file | if a W FORM contains '∅', AT LEAST ONE child M FORM must also contain '∅', AND the S-level original-tier FORM must contain '∅'. |
| V126 | `equal_sign_in_S_standard` | SOFT | file | '=' in S-level standard FORM, likely a leftover clitic boundary marker that should have been resolved. |
| V127 | `smart_quotes_in_FORM_hard` | HARD | file | smart-quote characters in any FORM (either tier). |
| V128 | `control_chars_in_FORM_TRANSL` | HARD | file | C0 control chars (<0x20 except \t \n \r) in FORM or TRANSL elements. |
| V129 | `asterisk_in_standard_FORM` | HARD | file | '*' in any FORM, either tier (original or standard). |
| V130 | `leading_trailing_whitespace_in_FORM` | HARD | file | FORM text has leading or trailing whitespace. |
| V131 | `zero_width_or_BOM_in_FORM_TRANSL` | HARD | file | zero-width or BOM in FORM or TRANSL. |
| V132 | `html_entities_in_FORM_TRANSL` | SOFT | file | HTML entity-like substrings in FORM or TRANSL. |
| V133 | `dash_in_S_standard_FORM` | SOFT | file | '-' in S-level standard FORM, likely a leftover segmentation/hyphenation marker that should have been removed. |
| V134 | `angle_brackets_in_S_FORM` | SOFT | file | '<' or '>' in S-level FORM at either tier. |
| V135 | `trailing_punct_mismatch` | SOFT | file | trailing-punct mismatch in S-level FORM pair. |
| V136 | `mixed_script_confusables` | SOFT | file | mixed Latin/Cyrillic/Greek scripts in FORM text. |
| V137 | `trailing_decimal_footnote_in_S_FORM_TRANSL` | SOFT | file | footnote-like substrings (`.<digits>` not preceded by a digit, or `<letter><digits>`) anywhere in any FORM (S/W/M, either kindOf) or any TRANSL element. |
| V138 | `superscript_digit_footnote` | SOFT | file | superscript digit (¹²³…) in FORM or TRANSL. |
| V139 | `bracketed_digit_footnote` | SOFT | file | bracketed-digit footnote in FORM or TRANSL. |
| V140 | `null_in_S_original_requires_child_W_and_M` | HARD | file | if an S-level FORM[@kindOf='original'] contains '∅', then S must have at least one child W with '∅' in some FORM, AND that same W must have at least one child M with '∅' in some FORM. |
| V141 | `W_reconstructs_S` | SOFT | file | the W FORMs of an S should spell the S FORM. |
| V142 | `unmarked_grammaticality` | SOFT | file | UNgrammaticality/marginality visible only informally. |
| V143 | `transl_language_script_mismatch` | SOFT | file | TRANSL script contradicts its declared language. |
| V146 | `phon_variant_group_malformed` | SOFT | file | malformed [x|y] variant group in a PHON. |
| V147 | `phon_legacy_tilde_variant` | SOFT | file | legacy x~y variant notation in a PHON. |

## `validate_glosses.py` — word/morpheme glossing

| Rule | Mnemonic | Severity | Scope | Checks |
| --- | --- | --- | --- | --- |
| V060 | `W_count_matches_word_count` | SOFT | file | count of <W> children of S should match the number of whitespace-delimited words in the S's FORM[@kindOf="original"]. |
| V061 | `M_count_matches_form_segmentation` | SOFT | file | count of <M> children of W should match the number of morphemes implied by the W's FORM segmentation markers (``-``, ``=``, ``<...>``). |
| V062 | `infix_M_needs_angle_gloss` | SOFT | file | an M whose FORM has infix shape ('-X-') should have a parent W with a TRANSL containing an angle-bracket gloss (e.g., '<AV>'). |
| V063 | `W_FORM_retains_segmentation` | — | file | when an S-level FORM[@kindOf='original'] carries more than 3 segmentation markers (``-``, ``=``, ``<``, ``>``), the W children's FORMs (both ``original`` and ``standard`` tiers) must collectively retain at least N/2 such markers each. |
| V064 | `every_M_has_TRANSL` | SOFT | file | every M element should have at least one TRANSL child. |
| V065 | `every_W_has_TRANSL` | SOFT | file | every W element should have at least one TRANSL child. |
| V066 | `clitic_in_W_requires_clitic_in_M` | HARD | file | if a W's preferred FORM contains '=' (clitic boundary) and the W has at least one child M, at least one of those child M FORMs (any kindOf, any tier) must also contain '='. |
| V067 | `no_angle_brackets_in_M_FORM` | HARD | file | no '<' or '>' in any M FORM, either tier. |
| V068 | `M_reconstructs_W` | SOFT | file | the M FORMs of a W should spell the W FORM. |
| V069 | `null_morpheme_in_W_requires_null_M` | HARD | file | if a W's preferred FORM contains a standalone null-morpheme marker '∅' (bordered by string edges, whitespace, or segmentation '-') and the W has at least one child M, then at least one child M FORM (any kindOf) must be exactly '∅'. |
| V070 | `gloss_code_as_FORM` | WARN | file | a W- or M-level FORM that is a bare gloss code. |
| V153 | `gloss_pieces_match_morphemes` | SOFT | file | a word's gloss should claim as many morphemes as its form does. |
| V154 | `gloss_script_matches_language` | SOFT | file | a gloss whose script its neighbours agree is wrong. |
| V155 | `gloss_language_set_incomplete` | SOFT | file | a glossed word should carry every gloss language the file uses. |

## `audit_gloss_scrape.py` — scrape-vs-source audit

| Rule | Mnemonic | Severity | Scope | Checks |
| --- | --- | --- | --- | --- |
| G001 | `marker_skeleton_parity` | HARD | file | the notation of a W FORM must match that of its W TRANSL. |
| G002 | `M_count_matches_gloss_units` | SOFT | file | the number of M children should match the number of gloss units in the W TRANSL. |
| G003 | `internal_dash_in_M_FORM` | SOFT | file | an M FORM with an internal '-' has un-split segmentation. |
| G004 | `infix_root_reconstructed` | HARD | file | a W FORM containing '<X>' must have an M spelling its root. |
| G005 | `gloss_label_inventory` | WARN | file | rare gloss labels one edit away from a frequent one. |
| G006 | `non_canonical_null_symbol` | HARD | file | null morphemes must be written '∅' (U+2205). |
| G007 | `marker_type_mismatch` | SOFT | file | FORM and TRANSL agree on segmentation but not marker type. |
| G010 | `mixed_marker_retention` | WARN | file | S-original tiers inconsistently retain segmentation markers. |
| G011 | `unsplit_slash_alternate` | SOFT | file | '/' in an S-original whose W tier also carries '/'. |
| G012 | `trailing_paren_note_in_TRANSL` | SOFT | file | a trailing '(...)' in a TRANSL belongs in the notes attribute. |

91 rules.
