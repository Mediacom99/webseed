#!/usr/bin/env python3
"""webseed — Genera e deploya siti per business locali senza website."""

import argparse
import csv
import os
from datetime import datetime

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="webseed — pipeline siti per business locali"
    )
    parser.add_argument(
        "--location", required=True,
        help='Es: "Garbagnate Milanese, Italy"',
    )
    parser.add_argument(
        "--query", required=True,
        help='Tipo di business: "ristorante", "parrucchiere", ecc.',
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="Max business da processare (default: 10)",
    )
    parser.add_argument(
        "--output", default="results.csv",
        help="File CSV output (default: results.csv)",
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Esegui smoke test Playwright dopo deploy",
    )
    parser.add_argument(
        "--no-deploy", action="store_true",
        help="Genera siti senza deploy su Vercel",
    )
    parser.add_argument(
        "--results-dir", default="results",
        help="Directory output (default: results/)",
    )
    args = parser.parse_args()

    # Env vars
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    vercel_token = os.getenv("VERCEL_TOKEN")

    required_missing = not maps_key or not anthropic_key
    if not args.no_deploy and not vercel_token:
        required_missing = True
    if required_missing:
        print("❌ Mancano variabili d'ambiente. Copia .env.example in .env e compila.")
        raise SystemExit(1)

    # Load prompt template
    prompt_path = os.path.join(os.path.dirname(__file__) or ".", "prompts", "site_gen.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Import modules
    import maps
    import generator
    if not args.no_deploy:
        import deployer

    print(f"\n🌱 webseed starting...")
    print(f"   Query: {args.query} in {args.location}")
    print(f"   Limit: {args.limit} business\n")

    # 1. Search businesses
    print("🔍 Ricerca business su Maps...")
    businesses = maps.search(
        query=args.query,
        location=args.location,
        limit=args.limit,
        api_key=maps_key,
        output_dir=args.results_dir,
    )
    print(f"\n✓ Trovati {len(businesses)} business senza sito\n")

    if not businesses:
        print("Nessun business trovato. Prova con una query o location diversa.")
        return

    # 2. CSV setup
    csv_fields = [
        "name", "address", "phone", "rating", "reviews",
        "category", "vercel_url", "maps_url", "deployed_at",
    ]
    csv_exists = os.path.exists(args.output)
    csv_file = open(args.output, "a", newline="", encoding="utf-8")
    csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
    if not csv_exists:
        csv_writer.writeheader()

    # 3. Process each business
    processed = 0
    for i, biz in enumerate(businesses, 1):
        print(f"[{i}/{len(businesses)}] {biz.name}")

        try:
            # Generate site
            print("  🤖 Generating site...")
            site_dir = generator.generate(
                biz, args.results_dir, prompt_template, anthropic_key
            )

            # Deploy
            if args.no_deploy:
                url = f"file://{os.path.abspath(os.path.join(site_dir, 'index.html'))}"
                print(f"  📂 {url}")
            else:
                print("  🚀 Deploying to Vercel...")
                url = deployer.deploy(site_dir, vercel_token)
                print(f"  ✅ {url}")

            # Optional smoke test
            if args.test:
                import tester

                safe_name = biz.name.lower().replace(" ", "_")[:30]
                test_result = tester.smoke_test(
                    url, safe_name,
                    os.path.join(args.results_dir, "screenshots"),
                )
                status = "✅" if test_result["ok"] else "⚠️"
                detail = "ok" if test_result["ok"] else test_result.get("error")
                print(f"  {status} Smoke test: {detail}")

            # Write CSV row
            csv_writer.writerow({
                "name": biz.name,
                "address": biz.address,
                "phone": biz.phone or "",
                "rating": biz.rating,
                "reviews": biz.reviews,
                "category": biz.category,
                "vercel_url": url,
                "maps_url": biz.maps_url,
                "deployed_at": datetime.now().isoformat(),
            })
            csv_file.flush()
            processed += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")

        print()

    csv_file.close()
    print(f"🎉 Done! {processed}/{len(businesses)} siti processati.")
    print(f"📊 Risultati salvati in: {args.output}")


if __name__ == "__main__":
    main()
