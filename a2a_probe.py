import asyncio, json, sys
from lan_a2a.client import send_text, fetch_card

async def main():
    out = {}
    # reverse: is .13 reachable from .14? (caller runs on .14 normally; here we test from .13)
    for name, url, tok in [
        ("agent-b 8114", "http://192.168.1.14:8114", None),
        ("lan-14 9902", "http://192.168.1.14:9902", None),
        ("lan-14 9900", "http://192.168.1.14:9900", None),
    ]:
        try:
            card = await fetch_card(url, timeout=6)
            out[name] = f"card OK: {card.name}"
        except Exception as e:
            out[name] = f"card ERR {type(e).__name__}: {str(e)[:120]}"
    print(json.dumps(out, ensure_ascii=False, indent=1))

asyncio.run(main())
