from glosbe_pipeline import main

if __name__ == "__main__":
    import sys
    sys.argv.insert(1, "validate_language_direction")
    main()
