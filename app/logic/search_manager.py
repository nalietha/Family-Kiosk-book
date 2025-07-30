from datetime import datetime

class SearchManager:
    """
    Read-only search utility for people, pets, stories, etc.
    Can be pointed at in-memory lists or loaded data structures.
    """

    def __init__(self, people=None, pets=None, stories=None, photos=None, quizzes=None):
        """
        people, pets, stories, photos: List of dicts (from JSON or elsewhere)
        """
        self.people = people if people is not None else []
        self.pets = pets if pets is not None else []
        self.stories = stories if stories is not None else []
        self.photos = photos if photos is not None else []
        self.quizzes = quizzes if quizzes is not None else []

    # --- Person search ---
    def find_people_by_name(self, name, exact=False):
        """Return all people whose name or nick matches. Partial unless exact=True."""
        result = []
        name_lc = name.lower().strip()
        for p in self.people:
            names = [p.get("name", ""), p.get("nickname", "")]
            if not exact:
                # Partial/substring match
                if any(name_lc in (n or "").lower() for n in names):
                    result.append(p)
            else:
                # Exact match (case-insensitive)
                if any((n or "").lower() == name_lc for n in names):
                    result.append(p)
        return result

    def person_exists(self, name):
        """Return True if any person matches this name or nickname (partial match)."""
        return len(self.find_people_by_name(name)) > 0

    def get_person_summary(self, person):
        """Short summary for display in search/resolve dialogs."""
        birth = person.get('birth_date', '')
        death = person.get('death_date', '')
        status = "Deceased" if person.get("deceased") else "Living"
        nickname = person.get("nickname", "")
        return f"{person.get('name', '')} ({birth}-{death}) [{status}] {'[' + nickname + ']' if nickname else ''}"

    def get_people_by_ids(self, ids):
        """If your data uses unique IDs, fetch by list of ids."""
        return [p for p in self.people if p.get("id") in ids]

    # --- Pet search (expand as needed) ---
    def find_pets_by_name(self, name, exact=False):
        name_lc = name.lower().strip()
        return [pet for pet in self.pets if (name_lc == (pet.get("name", "") or "").lower())] if exact else \
               [pet for pet in self.pets if name_lc in (pet.get("name", "") or "").lower()]

    def pet_exists(self, name):
        return len(self.find_pets_by_name(name)) > 0

    # --- Generic photo filter ---
    def get_photo_by(self, key_name, search_value, exact=False):
        """
        Find all photos where field `key_name` matches `search_value`.
        - If the field is a string, supports partial/substring unless exact=True.
        - If the field is a list (e.g., tags), will check if any item matches (substring).
        - If the field doesn't exist, skips photo.
        """
        results = []
        sv = (search_value or "").lower().strip()
        for photo in self.photos:
            value = photo.get(key_name)
            if value is None:
                continue
            if isinstance(value, list):
                # Search in lists (tags, etc.)
                for v in value:
                    v_str = (str(v) or "").lower()
                    if (exact and v_str == sv) or (not exact and sv in v_str):
                        results.append(photo)
                        break
            else:
                v_str = (str(value) or "").lower()
                if (exact and v_str == sv) or (not exact and sv in v_str):
                    results.append(photo)
        return results

    # --- Some specific helpers for convenience ---
    def get_photo_by_filename(self, filename, exact=True):
        return self.get_photo_by("file", filename, exact=exact)

    def get_photo_by_tag(self, tag, exact=False):
        return self.get_photo_by("tags", tag, exact=exact)

    def get_photo_by_date(self, date_str, exact=True):
        return self.get_photo_by("date", date_str, exact=exact)

    def get_photo_by_desc(self, desc, exact=False):
        return self.get_photo_by("desc", desc, exact=exact)

    # Optionally, you can expose a generic function as well:
    def get_photo_by_key(self, key_name, search_value, exact=False):
        """Alias for get_photo_by, with name to match your spec."""
        return self.get_photo_by(key_name, search_value, exact=exact)
    
    
    def get_items_by_date_range(self, items, start_date, end_date, date_key="date"):
        """
        Generalized date range search for any collection of dicts.
        - items: list of dicts (e.g. self.photos, self.stories, etc.)
        - start_date, end_date: strings 'YYYY-MM-DD'
        - date_key: key to look up date string in each dict
        """
        try:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        except Exception as e:
            raise ValueError("Invalid date format. Use YYYY-MM-DD") from e

        results = []
        for item in items:
            date_str = item.get(date_key, "")
            try:
                item_date = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                continue  # skip if missing or invalid
            if dt_start <= item_date <= dt_end:
                results.append(item)
        return results

    # --- Convenience wrappers ---
    def get_photos_by_date_range(self, start_date, end_date):
        return self.get_items_by_date_range(self.photos, start_date, end_date, date_key="date")

    def get_stories_by_date_range(self, start_date, end_date):
        return self.get_items_by_date_range(self.stories, start_date, end_date, date_key="date")
    
    # TODO: Add quizzes

    # --- Quiz Search ---
    # Quizzes are only searchable by tag or name. 
    # Quizzes should not be searchable by people names
    