from glosbe_pipeline import main

if __name__ == "__main__":
    import sys
    sys.argv.insert(1, "extract_iapi3_json")
    main()
