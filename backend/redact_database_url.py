import os
import re
url = os.environ.get("RESTORE_TARGET_DATABASE_URL", "")
print(re.sub(r"(://)[^/@]+:[^/@]*@", r"\1[redacted]@", url))
