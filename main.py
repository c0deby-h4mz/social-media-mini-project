import csv, os, hashlib
from datetime import datetime

# ============================================================
# STRUKTUR DATA 1: Linked List (untuk Feed Post)
# ============================================================
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        cur = self.head
        while cur.next:
            cur = cur.next
        cur.next = new_node

    def to_list(self):
        result, cur = [], self.head
        while cur:
            result.append(cur.data)
            cur = cur.next
        return result

# ============================================================
# STRUKTUR DATA 2: Stack (untuk Notifikasi Aktivitas)
# ============================================================
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def is_empty(self):
        return len(self.items) == 0

    def display_all(self):
        if self.is_empty():
            print("  Tidak ada notifikasi.")
            return
        print("=== NOTIFIKASI (Terbaru) ===")
        for item in reversed(self.items[-10:]):
            print(f"  • {item}")

# ============================================================
# DATABASE CSV & INISIALISASI
# ============================================================
USERS_FILE  = "users.csv"
POSTS_FILE  = "posts.csv"
FOLLOWS_FILE = "follows.csv"

def init_db():
    if not os.path.exists(USERS_FILE):
        _write_csv(USERS_FILE, [], ['id','username','password','bio'])
    if not os.path.exists(POSTS_FILE):
        _write_csv(POSTS_FILE, [], ['id','username','content','likes','timestamp'])
    if not os.path.exists(FOLLOWS_FILE):
        _write_csv(FOLLOWS_FILE, [], ['follower','following'])

def _read_csv(file):
    if not os.path.exists(file): return []
    with open(file, 'r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def _write_csv(file, data, fields):
    with open(file, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(data)

def _hash(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

# ============================================================
# STRUKTUR DATA 3: Hash Map – Cache User (O(1) lookup)
# ============================================================
user_cache = {}

def _load_cache():
    global user_cache
    user_cache = {u['username']: u for u in _read_csv(USERS_FILE)}

# ============================================================
# FITUR USER – CREATE / READ / UPDATE
# ============================================================
def register(uname, pwd, bio=""):
    _load_cache()
    if uname in user_cache:
        print("  [!] Username sudah digunakan!"); return False
    users = _read_csv(USERS_FILE)
    users.append({'id': str(len(users)+1), 'username': uname,
                  'password': _hash(pwd), 'bio': bio})
    _write_csv(USERS_FILE, users, ['id','username','password','bio'])
    _load_cache()
    print(f"  [✓] Registrasi berhasil! Selamat datang, @{uname}."); return True

def login(uname, pwd):
    _load_cache()
    u = user_cache.get(uname)
    if not u: print("  [!] Username tidak ditemukan!"); return None
    if u['password'] == _hash(pwd):
        print(f"  [✓] Login berhasil! Selamat datang, @{uname}."); return u
    print("  [!] Password salah!"); return None

def update_bio(uname, bio):
    users = _read_csv(USERS_FILE)
    for u in users:
        if u['username'] == uname: u['bio'] = bio; break
    _write_csv(USERS_FILE, users, ['id','username','password','bio'])
    _load_cache(); print("  [✓] Bio berhasil diperbarui!")

# ============================================================
# FITUR POST – CRUD PENUH
# ============================================================
def create_post(uname, content, notif: Stack):
    posts = _read_csv(POSTS_FILE)
    new_post = {'id': str(len(posts)+1), 'username': uname,
                'content': content, 'likes': '0',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")}
    posts.append(new_post)
    _write_csv(POSTS_FILE, posts, ['id','username','content','likes','timestamp'])
    notif.push(f"Post baru dibuat: '{content[:40]}'")
    print("  [✓] Post berhasil dibuat!")

def get_feed(uname):                               # READ + Sorting (timestamp desc)
    follows  = _read_csv(FOLLOWS_FILE)
    following = {f['following'] for f in follows if f['follower'] == uname} | {uname}
    posts = _read_csv(POSTS_FILE)
    sorted_posts = sorted(posts, key=lambda x: x['timestamp'], reverse=True)  # SORTING
    feed = LinkedList()
    for p in sorted_posts:
        if p['username'] in following:
            feed.append(p)
    return feed

def update_post(post_id, uname, content):          # UPDATE
    posts = _read_csv(POSTS_FILE)
    found = False
    for p in posts:
        if p['id'] == post_id and p['username'] == uname:
            p['content'] = content; found = True; break
    if found:
        _write_csv(POSTS_FILE, posts, ['id','username','content','likes','timestamp'])
        print("  [✓] Post berhasil diperbarui!")
    else:
        print("  [!] Post tidak ditemukan atau bukan milik kamu!")

def delete_post(post_id, uname):                   # DELETE
    posts = _read_csv(POSTS_FILE)
    new_posts = [p for p in posts if not (p['id']==post_id and p['username']==uname)]
    if len(new_posts) < len(posts):
        _write_csv(POSTS_FILE, new_posts, ['id','username','content','likes','timestamp'])
        print(f"  [✓] Post #{post_id} berhasil dihapus!")
    else:
        print("  [!] Post tidak ditemukan atau bukan milik kamu!")

def like_post(post_id, notif: Stack):
    posts = _read_csv(POSTS_FILE)
    for p in posts:
        if p['id'] == post_id:
            p['likes'] = str(int(p['likes']) + 1)
            _write_csv(POSTS_FILE, posts, ['id','username','content','likes','timestamp'])
            notif.push(f"Kamu menyukai post #{post_id} oleh @{p['username']}")
            print(f"  [✓] Post disukai! Total ❤️ : {p['likes']}"); return
    print("  [!] Post tidak ditemukan!")

def search_posts(keyword):                         # SEARCHING (Linear Search)
    posts = _read_csv(POSTS_FILE)
    results = [p for p in posts
               if keyword.lower() in p['content'].lower()
               or keyword.lower() in p['username'].lower()]
    return sorted(results, key=lambda x: int(x['likes']), reverse=True)  # sort by likes

# ============================================================
# FITUR FOLLOW / UNFOLLOW
# ============================================================
def follow_user(follower, following, notif: Stack):
    if follower == following: print("  [!] Tidak bisa follow diri sendiri!"); return
    _load_cache()
    if following not in user_cache: print("  [!] User tidak ditemukan!"); return
    follows = _read_csv(FOLLOWS_FILE)
    if any(f['follower']==follower and f['following']==following for f in follows):
        print(f"  [!] Kamu sudah follow @{following}!"); return
    follows.append({'follower': follower, 'following': following})
    _write_csv(FOLLOWS_FILE, follows, ['follower','following'])
    notif.push(f"Kamu mulai mengikuti @{following}")
    print(f"  [✓] Berhasil follow @{following}!")

def unfollow_user(follower, following):
    follows = _read_csv(FOLLOWS_FILE)
    new_follows = [f for f in follows if not (f['follower']==follower and f['following']==following)]
    if len(new_follows) < len(follows):
        _write_csv(FOLLOWS_FILE, new_follows, ['follower','following'])
        print(f"  [✓] Berhasil unfollow @{following}!")
    else:
        print(f"  [!] Kamu tidak mengikuti @{following}!")

# ============================================================
# TAMPILAN HELPER
# ============================================================
def print_post(p, idx=None):
    prefix = f"[{idx}] " if idx else "    "
    print(f"{prefix}@{p['username']}  |  {p['timestamp']}  |  ❤️  {p['likes']}")
    print(f"     {p['content'][:80]}")
    print(f"     Post ID: #{p['id']}")
    print()

def divider(title=""):
    print(f"\n{'='*50}")
    if title: print(f"  {title}"); print(f"{'='*50}")

# ============================================================
# MAIN – CLI MENU
# ============================================================
def main():
    init_db()
    notif = Stack()
    user  = None
    divider(" MINI SOCIAL MEDIA – Flat CSV Edition")

    while True:
        if not user:
            print("\n[1] Login   [2] Register   [0] Keluar")
            c = input("Pilih: ").strip()
            if   c == '1': user = login(input("  Username: ").strip(), input("  Password: ").strip())
            elif c == '2': register(input("  Username: ").strip(), input("  Password: ").strip(), input("  Bio (opsional): ").strip())
            elif c == '0': print("Sampai jumpa! 👋"); break
        else:
            divider(f"Halo, @{user['username']}!")
            print("[1] Feed      [2] Buat Post   [3] Edit Post  [4] Hapus Post")
            print("[5] Like Post [6] Follow       [7] Unfollow   [8] Cari Post")
            print("[9] Notifikasi [10] Edit Bio   [0] Logout")
            c = input("Pilih: ").strip()

            if   c == '1':
                feed  = get_feed(user['username'])
                posts = feed.to_list()
                divider(f"FEED  ({len(posts)} post)")
                [print_post(p, i+1) for i, p in enumerate(posts)] if posts else print("  Feed kosong. Follow lebih banyak orang!")
            elif c == '2':
                content = input("  Isi post: ").strip()
                if content: create_post(user['username'], content, notif)
            elif c == '3':
                update_post(input("  ID Post: ").strip(), user['username'], input("  Konten baru: ").strip())
            elif c == '4':
                delete_post(input("  ID Post: ").strip(), user['username'])
            elif c == '5':
                like_post(input("  ID Post: ").strip(), notif)
            elif c == '6':
                follow_user(user['username'], input("  Username target: ").strip(), notif)
            elif c == '7':
                unfollow_user(user['username'], input("  Username target: ").strip())
            elif c == '8':
                kw = input("  Kata kunci: ").strip()
                res = search_posts(kw)
                divider(f"HASIL CARI '{kw}'  ({len(res)} post)")
                [print_post(p, i+1) for i, p in enumerate(res)] if res else print("  Tidak ada hasil.")
            elif c == '9': divider("NOTIFIKASI"); notif.display_all()
            elif c == '10': update_bio(user['username'], input("  Bio baru: ").strip())
            elif c == '0': print(f"  Logout @{user['username']}. Sampai jumpa!"); user = None; notif = Stack()

if __name__ == "__main__":
    main()