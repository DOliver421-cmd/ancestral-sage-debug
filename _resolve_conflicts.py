"""Resolve remaining merge conflict markers in backend/server.py"""
import re

with open('backend/server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith('<<<<<<<'):
        # Collect HEAD section, separator, REMOTE section, closing marker
        head_lines = []
        remote_lines = []
        in_head = True
        i += 1
        while i < len(lines):
            l = lines[i]
            if l.startswith('======='):
                in_head = False
                i += 1
                continue
            if l.startswith('>>>>>>>'):
                i += 1
                break
            if in_head:
                head_lines.append(l)
            else:
                remote_lines.append(l)
            i += 1

        head = ''.join(head_lines)
        remote = ''.join(remote_lines)

        # --- Conflict-specific resolution rules ---

        # C-2 token revocation: remote has the more complete implementation
        # (adds session_id check + safe int conversion). Keep remote.
        if 'token_version' in head and 'token_version' in remote:
            output.extend(remote_lines)

        # Conflict 2: register route vs health/ready endpoint
        # Both are needed. Keep both: register route first, then health/ready.
        elif '/auth/register' in head and '/health/ready' in remote:
            output.extend(head_lines)
            output.extend(remote_lines)

        # Conflict 3: register route body vs /health/ready docstring content
        # These are interleaved because git split one logical block oddly.
        # The HEAD section is the register route body (self-registration logic).
        # The REMOTE section is part of the /health/ready docstring.
        # Keep HEAD (register body); remote docstring already captured above.
        elif 'self-registration is always a student' in head:
            output.extend(head_lines)

        # Conflict 4: cipher_tts code vs health/ready body
        # HEAD: cipher_tts tier 2 routing (keep)
        # REMOTE: health/ready endpoint body (keep - it continues after the marker)
        elif 'cipher_tts T2 openai' in head:
            output.extend(head_lines)
            # remote section is health/ready body -- keep it too, it's orphaned
            output.extend(remote_lines)

        # Conflict 5: WAI pipeline section vs platform_liveness endpoint
        # Both are needed. Keep both.
        elif 'WAI AUTONOMOUS PIPELINE' in head and 'platform_liveness' in remote:
            output.extend(head_lines)
            output.extend(remote_lines)

        # Conflict 6: platform_liveness doc vs port number
        # HEAD has the dict building block, REMOTE has the port number
        elif 'poor_righteous_teacher' in head and 'PORT' in remote:
            output.extend(head_lines)
            output.extend(remote_lines)

        # Conflict: port number default — remote uses 8001 (server default). Keep remote.
        elif "PORT" in head and "PORT" in remote and '8000' in head and '8001' in remote:
            output.extend(remote_lines)

        # Fallback: keep HEAD
        else:
            output.extend(head_lines)
    else:
        output.append(line)
        i += 1

result = ''.join(output)
remaining = result.count('<<<<<<<')
print(f'Conflict markers remaining: {remaining}')

# Show any remaining markers for debugging
if remaining > 0:
    for idx, l in enumerate(result.splitlines(), 1):
        if '<<<<<<<' in l or '=======' in l or '>>>>>>>' in l:
            print(f'  Line {idx}: {l[:80]}')

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(result)
print('Written.')
