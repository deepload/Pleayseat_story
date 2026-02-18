# Chapter 13: OSINT Deep Dive -- Finding Clara's Breadcrumbs

**Playseat Advanced Field Manual** | **Platform v0.2.0**
**Classification: UNCLASSIFIED** | **218 Crates, 225 Migrations, 1100+ Tables, 212 Routes**

> "Give me a domain name and 48 hours. I'll give you the threat actor's favorite pizza topping. But give me a reason to find someone I love, and I'll tear the entire open-source internet apart in six."

---

## 13.1 This Isn't an Exercise Anymore

**2026-02-18T11:00:00Z -- My apartment. Second pot of coffee. Hands steady now.**

I've been doing OSINT since before it had a fancy name. Back then we called it "Googling stuff." The difference now is scale, automation, and the ability to correlate across 14 different source types simultaneously. Playseat's OSINT module doesn't replace the analyst -- it amplifies them. Where a human analyst might take three days to profile a target, Playseat does the initial collection in minutes and presents the analyst with structured data instead of a pile of browser tabs.

But this time, I'm not profiling a threat actor. I'm looking for Clara.

Clara Dubois. French cryptographer. DGSE deep-cover analyst embedded in the Global Children's Aid Foundation. The woman who discovered PHANTOM MERCY's supply chain infection, documented it with the precision of a surgeon, sent me the evidence, and then went dark.

Gone dark doesn't mean dead. It means she stopped communicating through her established channels. It means her Signal dead-drop went silent. It means the Tor relay she used to route messages to me stopped forwarding. It could mean she's been compromised. It could mean she's deeper undercover than before. It could mean she's running.

I'm about to find out which one. And I'm going to do it using nothing but open-source intelligence, because I don't have access to DGSE's classified systems, and even if I did, I wouldn't trust them right now. If PHANTOM MERCY has insiders -- and the maintainer takeover in Chapter 12 proved they recruit insiders -- then any classified system might be compromised.

Open source. Verifiable. No backdoors. Let's go.

---

## 13.2 Creating Clara's OSINT Profile

Every investigation begins with a target profile. This structures all the intelligence I'll collect. I need to be careful here -- Clara is a friendly, not a hostile. But the OSINT techniques are the same. The difference is in the intent.

```bash
# Create a campaign to track the search for Clara
CAMPAIGN_ID="01951c01-aa01-7000-8000-000000000001"

# Create an OSINT target profile for Clara's trail
curl -s -X POST http://localhost:3000/api/v1/osint/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01951c01-aa01-7000-8000-000000000001",
    "target_name": "Clara Dubois (FRIENDLY -- LOCATE AND VERIFY SAFETY)",
    "organization": "Global Childrens Aid Foundation / DGSE (deep cover)",
    "aliases": ["C. Dubois", "Claire Martin", "Dr. Dubois", "Analyst Nightingale"],
    "source_types": ["social_media", "domain_whois", "dns_records", "certificate_transparency", "code_repository", "paste_site", "dark_web_forum", "news_media", "public_records", "job_postings"]
  }' | jq .
```

**Response:**

```json
{
  "id": "01951c05-bb02-7000-8000-000000000002",
  "campaign_id": "01951c01-aa01-7000-8000-000000000001",
  "entity_type": "Person",
  "primary_name": "Clara Dubois (FRIENDLY -- LOCATE AND VERIFY SAFETY)",
  "aliases": ["C. Dubois", "Claire Martin", "Dr. Dubois", "Analyst Nightingale"],
  "summary": "OSINT profile for friendly locate operation -- Clara Dubois",
  "exposure_level": "Low",
  "confidence_score": 0.35,
  "source_count": 7,
  "finding_count": 4,
  "digital_footprint": {
    "domains": [],
    "ip_addresses": [],
    "certificates": 0,
    "code_repos": 0,
    "paste_mentions": 1
  },
  "social_footprint": {
    "accounts": ["gcaf_staff_directory"],
    "mentions": 3,
    "connections": 2
  },
  "corporate_footprint": {
    "registrations": 0,
    "patents": 1,
    "filings": 0
  },
  "created_at": "2026-02-18T11:05:00Z",
  "updated_at": "2026-02-18T11:05:00Z"
}
```

Low exposure level. Confidence score of 0.35. That's Clara -- she's a trained intelligence officer. Her digital footprint is almost nonexistent. No personal domains. No personal IP infrastructure. No certificates. One patent (her doctoral work on post-quantum lattice cryptography, published under her real name before she went undercover). One paste mention. Three social media mentions. Two social connections.

This is going to be hard. Finding someone who doesn't want to be found is always hard. Finding someone who was trained by the DGSE to not be found is a whole different level.

But Clara left breadcrumbs. She's too smart not to. If she's alive and free, she left a trail that only I would recognize. I just have to find it.

---

## 13.3 Social Media: The GCAF Staff Directory

Let's start with what's public. GCAF has a website. They have social media. They post about their operations. If Clara was embedded there as an aid worker, she'll appear in their public communications.

```bash
# Search social media and organizational sources
curl -s -X POST http://localhost:3000/api/v1/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "Clara Dubois",
    "organization": "Global Childrens Aid Foundation",
    "source_types": ["social_media", "news_media"],
    "max_results": 30
  }' | jq '.[] | {source_type, title, content, confidence}'
```

```json
[
  {
    "source_type": "SocialMedia",
    "title": "GCAF Twitter: Team spotlight -- Marseille distribution center",
    "content": "Post: @GCAFGlobal (2026-01-28): 'Our Marseille team processed 1,200 aid packages this week! Huge thanks to our logistics coordinator Clara and the entire warehouse team. #AidWorks #Marseille'\nImage: Group photo, warehouse setting, 8 people in GCAF vests\nGeo-tag: Marseille, France (43.2965, 5.3698)\nEngagement: 47 likes, 12 retweets, 3 replies",
    "confidence": 0.72
  },
  {
    "source_type": "SocialMedia",
    "title": "GCAF Instagram: Marseille operations gallery",
    "content": "Post: @gcaf_official (2026-01-30): 'Behind the scenes at our Marseille hub. Every package tells a story. Every story matters.'\nImages: 6-photo carousel, warehouse operations\nImage 4 of 6: Background figure matching Clara Dubois profile -- dark hair, mid-30s, wearing GCAF lanyard, reviewing clipboard near loading dock\nGeo-tag: Marseille, France\nEngagement: 89 likes, 5 comments",
    "confidence": 0.68
  },
  {
    "source_type": "SocialMedia",
    "title": "LinkedIn: Claire Martin -- Logistics Coordinator, GCAF",
    "content": "Profile: Claire Martin\nTitle: Logistics Coordinator at Global Children's Aid Foundation\nLocation: Marseille, France\nEducation: MSc Applied Mathematics, Universite de Lyon (2016)\nExperience: GCAF (2024-present), Medecins Sans Frontieres (2020-2024), UN OCHA (2018-2020)\nSkills: Supply chain logistics, data analysis, French, English, Arabic\nConnections: 127\nLast active: 2026-02-01\nProfile photo: Professional headshot, dark hair, angular features",
    "confidence": 0.75
  },
  {
    "source_type": "NewsMedia",
    "title": "La Provence: GCAF opens expanded Marseille distribution center",
    "content": "Article (2026-01-15): The Global Children's Aid Foundation inaugurated its expanded distribution center in the Joliette district of Marseille on Monday. The facility will serve as a hub for humanitarian shipments to North Africa and the Eastern Mediterranean. GCAF logistics coordinator Claire Martin (pictured, third from left) said the expansion would allow the organization to process 40% more shipments per month.\nPhoto: Ribbon cutting ceremony, 5 GCAF staff with local officials\nPerson matching Clara profile: Third from left, dark business attire, GCAF badge",
    "confidence": 0.80
  }
]
```

There she is. Cover name: Claire Martin. Location: Marseille. Role: Logistics Coordinator. Last active on LinkedIn: February 1st.

She went dark on February 12th, when she sent me the SBOM. That's 11 days between her last public appearance and her last communication with me. And the GCAF Twitter post from January 28th puts her in the Marseille warehouse -- the same warehouse that processes the manifests she found compromised.

She was working inside the machine. Documenting it from the inside. And then she sent me everything and disappeared.

### The Photo

I need to look at the Instagram post more carefully.

```bash
# Deep dive on the GCAF Instagram post
curl -s -X POST http://localhost:3000/api/v1/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "GCAF Instagram 2026-01-30 Marseille",
    "organization": "Global Childrens Aid Foundation",
    "source_types": ["social_media"],
    "max_results": 5
  }' | jq '.[0].content'
```

Image 4 of 6. Background figure. Reviewing a clipboard near the loading dock.

There she was. Thinner than I remembered. Same defiant eyes.

Clara always stood like that -- slightly apart from the group, weight on her back foot, ready to move. It's a DGSE thing, she told me once. "Always know your exits." She was joking. She wasn't joking.

The geo-tag confirms Marseille. The date is January 30th -- 13 days before she went dark. She was still operational. Still in position. Still doing her job while simultaneously mapping a child trafficking network's software supply chain.

I can't think about how brave that is right now. I need to keep working.

---

## 13.4 WHOIS and DNS: Shell Companies Connected to PHANTOM MERCY

Clara's SBOM pointed to several domains used by PHANTOM MERCY's infrastructure. I need to trace them through WHOIS and DNS to find connections to Meridian Consulting Group (the financial SPOF from Chapter 12) and any other shell companies.

```bash
# Search WHOIS for PHANTOM MERCY infrastructure domains
curl -s -X POST http://localhost:3000/api/v1/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "pm-ops.example",
    "organization": null,
    "source_types": ["domain_whois", "dns_records"],
    "max_results": 20
  }' | jq .
```

**Response:**

```json
[
  {
    "id": "01951c10-cc03-7000-8000-000000000010",
    "source_type": "DomainWhois",
    "source_name": "WHOIS Lookup",
    "source_url": "https://whois.synth-provider.example/pm-ops.example",
    "title": "WHOIS: pm-ops.example",
    "content": "Domain: pm-ops.example\nRegistrar: SynthRegistrar Cyprus Ltd\nRegistered: 2025-08-15\nExpires: 2026-08-15\nRegistrant: Meridian Digital Solutions Ltd\nRegistrant Email: admin@meridian-solutions.example\nRegistrant Address: 42 Archbishop Makarios III Avenue, Nicosia, Cyprus\nNameservers: ns1.cloudflare-cdn.example, ns2.cloudflare-cdn.example\nDNSSEC: unsigned\nStatus: clientTransferProhibited",
    "confidence": 0.95,
    "collected_at": "2026-02-18T11:15:00Z"
  },
  {
    "id": "01951c10-cc03-7000-8000-000000000011",
    "source_type": "DomainWhois",
    "source_name": "WHOIS Lookup",
    "source_url": "https://whois.synth-provider.example/mcg-consulting.example",
    "title": "WHOIS: mcg-consulting.example",
    "content": "Domain: mcg-consulting.example\nRegistrar: SynthRegistrar Cyprus Ltd\nRegistered: 2025-06-20\nExpires: 2026-06-20\nRegistrant: Meridian Consulting Group Ltd\nRegistrant Email: info@mcg-consulting.example\nRegistrant Address: 42 Archbishop Makarios III Avenue, Nicosia, Cyprus\nNameservers: ns1.cloudflare-cdn.example, ns2.cloudflare-cdn.example\nDNSSEC: unsigned\nStatus: active",
    "confidence": 0.95,
    "collected_at": "2026-02-18T11:15:05Z"
  },
  {
    "id": "01951c10-cc03-7000-8000-000000000012",
    "source_type": "DnsRecords",
    "source_name": "DNS Resolution",
    "source_url": null,
    "title": "DNS: pm-ops.example",
    "content": "A: 198.51.100.42 (Cloudflare Workers)\nAAAA: (none)\nMX: (none)\nTXT: v=spf1 -all\nNS: ns1.cloudflare-cdn.example, ns2.cloudflare-cdn.example\nSOA: ns1.cloudflare-cdn.example dns.pm-ops.example 2025081501",
    "confidence": 0.98,
    "collected_at": "2026-02-18T11:15:10Z"
  }
]
```

Same address. 42 Archbishop Makarios III Avenue, Nicosia, Cyprus. Both `pm-ops.example` (the DNS tunneling relay) and `mcg-consulting.example` (the donor portal exfiltration endpoint) are registered to entities at the same physical address. Same registrar. Same Cloudflare nameservers.

Meridian Digital Solutions. Meridian Consulting Group. Two shell companies, one address, one operation. The purple team exercise in Chapter 12 identified Meridian as the financial SPOF. Now OSINT confirms the infrastructure connection.

---

## 13.5 Certificate Transparency: Hidden Infrastructure

Every TLS certificate issued by a public Certificate Authority gets logged to CT logs. This means I can find every subdomain that has ever been issued a certificate, including ones PHANTOM MERCY might not have intended to be public.

```bash
# Search CT logs for Meridian infrastructure
curl -s -X POST http://localhost:3000/api/v1/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "meridian",
    "source_types": ["certificate_transparency"],
    "max_results": 50
  }' | jq '.[] | {title, content, confidence}'
```

```json
{
  "title": "CT Log: *.mcg-consulting.example certificates",
  "content": "Certificate 1:\n  Subject: mcg-consulting.example\n  Issuer: Let's Encrypt R3\n  Valid: 2025-06-20 to 2025-09-18\n  Serial: 04:b1:c2:d3:e4:f5:06:17\n\nCertificate 2:\n  Subject: analytics.mcg-consulting.example\n  Issuer: Let's Encrypt R3\n  Valid: 2025-07-01 to 2025-09-29\n  Serial: 04:b2:c3:d4:e5:f6:07:18\n\nCertificate 3:\n  Subject: ledger.mcg-consulting.example\n  Issuer: Let's Encrypt R3\n  Valid: 2025-09-15 to 2025-12-14\n  Serial: 04:b3:c4:d5:e6:f7:08:19\n\nCertificate 4:\n  Subject: payments.meridian-solutions.example\n  Issuer: Let's Encrypt R3\n  Valid: 2025-10-01 to 2025-12-30\n  Serial: 04:b4:c5:d6:e7:f8:09:20\n\nCertificate 5:\n  Subject: ops.pm-network.example\n  Issuer: Let's Encrypt R3\n  Valid: 2025-11-01 to 2026-01-30\n  Serial: 04:b5:c6:d7:e8:f9:10:21",
  "confidence": 0.97
}
```

Five certificates. Five subdomains I didn't know about:

1. `mcg-consulting.example` -- the shell company's public face
2. `analytics.mcg-consulting.example` -- the donor portal exfiltration endpoint (known)
3. `ledger.mcg-consulting.example` -- a financial ledger interface (new!)
4. `payments.meridian-solutions.example` -- a payment processing endpoint (new!)
5. `ops.pm-network.example` -- an operations dashboard for the entire PHANTOM MERCY network (new!)

That `ops.pm-network.example` is the big one. An operations dashboard. If I can find cached versions of that page, screenshots, or any public exposure, I might be able to map PHANTOM MERCY's entire organizational structure.

---

## 13.6 Dark Web Monitoring: Encrypted Messages

This is where it gets personal. I set up dark web monitoring specifically to look for communications that match Clara's writing style. She has tells -- the way she structures sentences, her preference for mathematical metaphors, her habit of ending critical observations with rhetorical questions.

```bash
# Search dark web sources
curl -s -X POST http://localhost:3000/api/v1/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "Clara Dubois",
    "source_types": ["dark_web_forum", "paste_site"],
    "max_results": 20
  }' | jq '.[] | {source_type, title, content, confidence}'
```

```json
[
  {
    "source_type": "DarkWebForum",
    "title": "Encrypted message: Dread forum, humanitarian sector subforum",
    "content": "Forum: Dread (onion)\nSubforum: /d/humanitarian_security\nThread: 'Supply chain integrity in aid logistics'\nPost date: 2026-02-14 (2 days after Clara went dark)\nAuthor: nightingale_42\nContent (excerpt): 'The dependency graph is a map. Every node is a decision. Every edge is trust. But what happens when the trust is manufactured? What happens when the node at depth three is not what it claims to be? The answer is not in the code. The answer is in who pays for the code. Follow the financial edges, not the technical ones. The graph always tells the truth if you read it correctly.'\nPGP signed: Yes (key ID: 0xDEAD...CAFE)\nReply count: 0",
    "confidence": 0.65
  },
  {
    "source_type": "PasteSite",
    "title": "PrivateBin: Encrypted paste with specific metadata",
    "content": "Paste service: PrivateBin (onion mirror)\nPaste date: 2026-02-15\nExpiration: 7 days (expires 2026-02-22)\nBurn after reading: No\nContent: PGP encrypted block (2048 bytes)\nRecipient key fingerprint: Matches protagonist's public key\nSubject line (cleartext): 'For the analyst who builds cathedrals from data. Coordinates follow. -N'\nNote: 'N' is consistent with Clara's field alias 'Nightingale'",
    "confidence": 0.70
  },
  {
    "source_type": "DarkWebForum",
    "title": "Marketplace listing: PHANTOM MERCY operational data for sale",
    "content": "Forum: AlphaBay successor (onion)\nListing date: 2026-02-16\nSeller: ghost_meridian\nTitle: 'Humanitarian logistics platform access -- verified credentials'\nDescription: 'Full admin access to GCAF logistics platform. Includes manifest database, donor records, fleet GPS real-time feed. Price: 15 BTC. Escrow accepted.'\nNote: This listing appeared AFTER Clara went dark. Someone is selling the access she documented.",
    "confidence": 0.82
  }
]
```

Three results. Let me process them.

**Result 1: The Dread post.** Username: `nightingale_42`. Clara's field alias is Nightingale. The writing style -- mathematical metaphors, rhetorical questions, the phrase "the graph always tells the truth" -- that's Clara. I'd bet my career on it. She posted this two days after going dark. She's alive. She's still thinking about the investigation. And she's telling me, in her oblique way, to follow the money. "Follow the financial edges, not the technical ones."

**Result 2: The PrivateBin paste.** Encrypted to my public key. Subject line: "For the analyst who builds cathedrals from data." She called me that once, in Lyon, after I showed her the first version of Playseat's evidence chain system. "You build cathedrals from data," she said, laughing. Nobody else knows that. This is Clara. The paste contains coordinates. I need to decrypt it.

**Result 3: The marketplace listing.** Someone is selling GCAF platform access. `ghost_meridian` -- the username contains "meridian." This could be a PHANTOM MERCY operator liquidating assets after Clara's discovery compromised the operation. Or it could be a trap. Either way, it confirms that the GCAF compromise is active and being exploited.

---

## 13.7 Geolocation: Narrowing Clara's Position

I'm cross-referencing the social media data with the dark web timestamps to build a timeline of Clara's movements.

```bash
# Search for geographic indicators
curl -s -X POST http://localhost:3000/api/v1/osint/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "Clara Dubois Marseille",
    "organization": "Global Childrens Aid Foundation",
    "source_types": ["social_media", "news_media", "public_records"],
    "max_results": 20
  }' | jq '.[] | {source_type, title, content, confidence}'
```

```json
[
  {
    "source_type": "PublicRecords",
    "title": "GCAF Staff Directory (public web cache)",
    "content": "Source: Google Cache of gcaf.example/team (page modified 2026-01-20)\nEntry: Claire Martin, Logistics Coordinator\nOffice: Marseille Distribution Center, 15 Rue de la Joliette, 13002 Marseille\nPhone: +33 4 91 XX XX XX (redacted by platform)\nEmail: c.martin@gcaf.example\nPhoto: Professional headshot matching previous observations\nBio: 'Claire joined GCAF in 2024 after four years with MSF. She specializes in supply chain optimization for humanitarian logistics.'",
    "confidence": 0.88
  },
  {
    "source_type": "SocialMedia",
    "title": "GCAF Facebook: Marseille team building event",
    "content": "Post: GCAF Official Facebook (2026-02-05): 'Team building day in Calanques National Park! Our Marseille team took a well-deserved break to hike the calanques and enjoy the Mediterranean winter sun.'\nPhoto album: 12 photos\nPhoto 7: Background figure matching Clara/Claire profile on hiking trail, wearing sunglasses, navy jacket\nLocation tag: Calanque de Sormiou, Marseille\nDate: 2026-02-05 (7 days before she went dark)",
    "confidence": 0.62
  },
  {
    "source_type": "SocialMedia",
    "title": "GCAF Website: January 2026 newsletter",
    "content": "Source: gcaf.example/newsletter/2026-01\nSection: 'Marseille Hub Update'\nText: 'Our Marseille team processed a record 1,847 aid packages in January, thanks to the expanded facility and the tireless work of coordinator Claire Martin and her team of 12 volunteers.'\nAccompanying photo: Wide shot of warehouse, multiple workers, Claire/Clara visible at desk in background reviewing laptop\nDate: Published 2026-02-01",
    "confidence": 0.75
  }
]
```

Timeline building:

| Date | Source | Location | Activity |
|------|--------|----------|----------|
| 2026-01-15 | La Provence | Marseille, Joliette | Ribbon cutting, expanded warehouse |
| 2026-01-20 | GCAF staff directory | Marseille | Listed as logistics coordinator |
| 2026-01-28 | GCAF Twitter | Marseille warehouse | Team spotlight photo |
| 2026-01-30 | GCAF Instagram | Marseille warehouse | Background in operations photo |
| 2026-02-01 | GCAF Newsletter | Marseille | Mentioned in January update |
| 2026-02-01 | LinkedIn | Marseille | Last active on LinkedIn |
| 2026-02-05 | GCAF Facebook | Calanques, Marseille | Team building hike |
| 2026-02-12 | Signal dead-drop | Unknown | Sent SBOM and message to me |
| 2026-02-14 | Dread forum | Unknown (Tor) | Posted as nightingale_42 |
| 2026-02-15 | PrivateBin | Unknown (Tor) | Encrypted paste for me |

She was in Marseille consistently from January 15 through February 5. Then there's a 7-day gap before she sent the SBOM on February 12. Something happened in that gap. She either discovered something that accelerated her timeline, or she was discovered and had to move fast.

The Dread post on February 14 and the PrivateBin paste on February 15 confirm she's alive and operational after going dark. She's using Tor, which means she's either in a location where she can access the internet without attribution, or she's using a mobile connection with Tor bridges.

Southern France. She's still in southern France. Every indicator points to it. The GCAF Marseille hub is her operational base. She hasn't fled the country -- she's gone to ground locally.

---

## 13.8 Entity Resolution: Connecting Clara's World

Now I need to resolve the entities from multiple sources into a unified picture.

```bash
# Resolve entities from collected intelligence
curl -s -X POST http://localhost:3000/api/v1/osint/entities/resolve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01951c01-aa01-7000-8000-000000000001",
    "target_name": "Clara Dubois",
    "organization": "Global Childrens Aid Foundation"
  }' | jq .
```

**Response:**

```json
[
  {
    "id": "01951c20-dd04-7000-8000-000000000020",
    "entity_type": "Person",
    "canonical_name": "Clara Dubois / Claire Martin (SYNTHETIC)",
    "identifier_count": 8,
    "source_count": 7,
    "confidence": 0.88,
    "resolved_at": "2026-02-18T11:30:00Z"
  },
  {
    "id": "01951c20-dd04-7000-8000-000000000021",
    "entity_type": "Organization",
    "canonical_name": "Global Children's Aid Foundation (GCAF)",
    "identifier_count": 5,
    "source_count": 6,
    "confidence": 0.95,
    "resolved_at": "2026-02-18T11:30:00Z"
  },
  {
    "id": "01951c20-dd04-7000-8000-000000000022",
    "entity_type": "Organization",
    "canonical_name": "Meridian Consulting Group / Meridian Digital Solutions (PHANTOM MERCY front)",
    "identifier_count": 6,
    "source_count": 4,
    "confidence": 0.92,
    "resolved_at": "2026-02-18T11:30:00Z"
  },
  {
    "id": "01951c20-dd04-7000-8000-000000000023",
    "entity_type": "Person",
    "canonical_name": "nightingale_42 (Clara's Tor identity)",
    "identifier_count": 3,
    "source_count": 2,
    "confidence": 0.72,
    "resolved_at": "2026-02-18T11:30:00Z"
  },
  {
    "id": "01951c20-dd04-7000-8000-000000000024",
    "entity_type": "Infrastructure",
    "canonical_name": "PHANTOM MERCY C2/Financial Infrastructure",
    "identifier_count": 7,
    "source_count": 5,
    "confidence": 0.90,
    "resolved_at": "2026-02-18T11:30:00Z"
  }
]
```

Five entities resolved:
1. **Clara / Claire Martin** -- 8 identifiers across 7 sources, confidence 0.88
2. **GCAF** -- the humanitarian org she's embedded in
3. **Meridian** -- the PHANTOM MERCY financial front
4. **nightingale_42** -- Clara's Tor identity (linked to Clara with 0.72 confidence)
5. **PHANTOM MERCY infrastructure** -- the C2 and financial systems

---

## 13.9 Building the Relationship Graph

The graph is where OSINT becomes intelligence. Individual facts are data. Connections between facts are intelligence.

```bash
# Build the relationship graph
curl -s -X POST http://localhost:3000/api/v1/osint/graph/build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01951c01-aa01-7000-8000-000000000001",
    "target_name": "Clara Dubois",
    "organization": "Global Childrens Aid Foundation"
  }' | jq .
```

**Response:**

```json
{
  "id": "01951c30-ee05-7000-8000-000000000030",
  "campaign_id": "01951c01-aa01-7000-8000-000000000001",
  "name": "OSINT Graph: Clara Dubois / PHANTOM MERCY Investigation",
  "node_count": 14,
  "edge_count": 22,
  "cluster_count": 4,
  "nodes": [
    {
      "id": "01951c30-ee05-7000-8000-000000000031",
      "label": "Clara Dubois / Claire Martin",
      "entity_type": "Person",
      "centrality": 0.95,
      "influence": 0.90,
      "cluster_id": 0
    },
    {
      "id": "01951c30-ee05-7000-8000-000000000032",
      "label": "GCAF Marseille Hub",
      "entity_type": "Organization",
      "centrality": 0.82,
      "influence": 0.75,
      "cluster_id": 0
    },
    {
      "id": "01951c30-ee05-7000-8000-000000000033",
      "label": "nightingale_42",
      "entity_type": "Person",
      "centrality": 0.55,
      "influence": 0.50,
      "cluster_id": 1
    },
    {
      "id": "01951c30-ee05-7000-8000-000000000034",
      "label": "Meridian Consulting Group",
      "entity_type": "Organization",
      "centrality": 0.78,
      "influence": 0.85,
      "cluster_id": 2
    },
    {
      "id": "01951c30-ee05-7000-8000-000000000035",
      "label": "pm-ops.example",
      "entity_type": "Infrastructure",
      "centrality": 0.70,
      "influence": 0.65,
      "cluster_id": 3
    },
    {
      "id": "01951c30-ee05-7000-8000-000000000036",
      "label": "Marseille, France",
      "entity_type": "Location",
      "centrality": 0.88,
      "influence": 0.80,
      "cluster_id": 0
    },
    {
      "id": "01951c30-ee05-7000-8000-000000000037",
      "label": "42 Makarios III Ave, Nicosia",
      "entity_type": "Location",
      "centrality": 0.60,
      "influence": 0.55,
      "cluster_id": 2
    },
    {
      "id": "01951c30-ee05-7000-8000-000000000038",
      "label": "shadow-relay@1.0.3",
      "entity_type": "Infrastructure",
      "centrality": 0.65,
      "influence": 0.60,
      "cluster_id": 3
    }
  ],
  "edges": [
    { "source_id": "..031", "target_id": "..032", "relationship": "EmployedBy", "weight": 0.90 },
    { "source_id": "..031", "target_id": "..033", "relationship": "IsIdentity", "weight": 0.72 },
    { "source_id": "..031", "target_id": "..036", "relationship": "LocatedIn", "weight": 0.85 },
    { "source_id": "..032", "target_id": "..036", "relationship": "LocatedIn", "weight": 0.95 },
    { "source_id": "..032", "target_id": "..038", "relationship": "CompromisedBy", "weight": 0.88 },
    { "source_id": "..034", "target_id": "..037", "relationship": "RegisteredAt", "weight": 0.95 },
    { "source_id": "..034", "target_id": "..035", "relationship": "Operates", "weight": 0.90 },
    { "source_id": "..035", "target_id": "..038", "relationship": "Distributes", "weight": 0.85 }
  ]
}
```

Four clusters:
- **Cluster 0**: Clara's world (Clara, GCAF, Marseille)
- **Cluster 1**: Clara's dark web identity (nightingale_42)
- **Cluster 2**: PHANTOM MERCY financial operations (Meridian, Nicosia)
- **Cluster 3**: PHANTOM MERCY technical infrastructure (C2, shadow-relay)

The cross-cluster edges are the investigative gold:
- Clara (Cluster 0) --> nightingale_42 (Cluster 1): "IsIdentity" at 0.72 weight
- GCAF (Cluster 0) --> shadow-relay (Cluster 3): "CompromisedBy" at 0.88 weight
- Meridian (Cluster 2) --> pm-ops (Cluster 3): "Operates" at 0.90 weight

### Graph Analysis SQL

```sql
-- Find cross-cluster edges (the most important investigative leads)
SELECT
    g.name,
    src_node->>'label' AS source,
    tgt_node->>'label' AS target,
    edge->>'relationship' AS relationship,
    (edge->>'weight')::float AS weight
FROM osint_graphs g,
     jsonb_array_elements(g.edges) AS edge,
     jsonb_array_elements(g.nodes) AS src_node,
     jsonb_array_elements(g.nodes) AS tgt_node
WHERE src_node->>'id' = edge->>'source_id'
    AND tgt_node->>'id' = edge->>'target_id'
    AND src_node->>'cluster_id' != tgt_node->>'cluster_id'
ORDER BY (edge->>'weight')::float DESC;

-- Timeline reconstruction: all intelligence in chronological order
SELECT
    r.collected_at,
    r.source_type,
    r.title,
    LEFT(r.content, 200) AS content_preview,
    r.confidence
FROM osint_source_results r
WHERE r.profile_id = '01951c05-bb02-7000-8000-000000000002'
ORDER BY r.collected_at ASC;
```

---

## 13.10 Exposure Scoring: How Findable Is Clara?

This cuts both ways. Low exposure means I have trouble finding her. It also means PHANTOM MERCY has trouble finding her. I need to know whether she's safe.

```bash
# Get exposure score for Clara's profile
PROFILE_ID="01951c05-bb02-7000-8000-000000000002"

curl -s "http://localhost:3000/api/v1/osint/score/$PROFILE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "id": "01951c40-ff06-7000-8000-000000000040",
  "profile_id": "01951c05-bb02-7000-8000-000000000002",
  "overall_score": 38.5,
  "overall_level": "Medium",
  "digital_score": 25.0,
  "social_score": 45.0,
  "corporate_score": 15.0,
  "breach_score": 10.0,
  "risk_factors": [
    {
      "category": "social",
      "description": "Appears in multiple GCAF social media posts with geo-tagged locations",
      "severity": "High",
      "score_impact": 20.0
    },
    {
      "category": "social",
      "description": "LinkedIn profile with employment history and education details",
      "severity": "Medium",
      "score_impact": 15.0
    },
    {
      "category": "digital",
      "description": "Dark web posts under consistent pseudonym with identifiable writing style",
      "severity": "High",
      "score_impact": 15.0
    },
    {
      "category": "corporate",
      "description": "Listed in public GCAF staff directory with office location",
      "severity": "Medium",
      "score_impact": 10.0
    }
  ],
  "recommendations": [
    "GCAF social media posts with Clara/Claire should be reviewed for operational security",
    "LinkedIn profile should be deactivated or sanitized",
    "Dark web pseudonym nightingale_42 creates linkability risk",
    "Staff directory listing reveals workplace location",
    "Geo-tagged photos narrow location to specific district of Marseille"
  ],
  "scored_at": "2026-02-18T11:45:00Z"
}
```

Overall exposure: 38.5 -- Medium. Not terrible for a deep-cover operative, but the social media posts from GCAF are the biggest risk. Clara didn't control those posts. GCAF's comms team posted them without thinking about OPSEC. The geo-tagged warehouse location, the team building photos, the newsletter mentions -- all of it narrows Clara's location for anyone who's looking.

And after she documented PHANTOM MERCY's supply chain infection, someone is definitely looking.

The nightingale_42 pseudonym is a risk too. It's consistent across two dark web platforms, which means it creates linkability. If PHANTOM MERCY is monitoring humanitarian security forums -- and they'd be stupid not to -- they might connect nightingale_42's post about supply chain dependency graphs to the discovery of their shadow-relay package.

Clara knows all this. She's a trained intelligence officer. She used the pseudonym anyway. Which means the message was more important than the risk. She wanted someone to see it. She wanted *me* to see it.

---

## 13.11 The Intelligence Report

Time to put it all together.

```bash
# Generate the OSINT report
curl -s -X POST http://localhost:3000/api/v1/osint/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "01951c01-aa01-7000-8000-000000000001",
    "target_name": "Clara Dubois",
    "organization": "Global Childrens Aid Foundation"
  }' | jq .
```

**Response:**

```json
{
  "id": "01951c50-aa07-7000-8000-000000000050",
  "campaign_id": "01951c01-aa01-7000-8000-000000000001",
  "target_name": "Clara Dubois / Claire Martin",
  "executive_summary": "OSINT investigation into the whereabouts of Clara Dubois (cover name: Claire Martin), DGSE deep-cover analyst embedded in GCAF Marseille. Subject was active in Marseille through February 5, 2026. Sent classified intelligence (SBOM documenting PHANTOM MERCY supply chain compromise) on February 12 and ceased established communications. Dark web activity under pseudonym nightingale_42 on February 14-15 confirms subject is alive and operational. Encrypted communication (PrivateBin paste) directed at specific recipient suggests subject is attempting to re-establish contact through alternative channels. Geolocation analysis places subject in southern France with high confidence. Exposure score 38.5 (Medium) -- GCAF social media creates uncontrolled location exposure that may endanger subject.",
  "exposure_level": "Medium",
  "exposure_score": 38.5,
  "entity_count": 5,
  "finding_count": 12,
  "findings": [
    {
      "title": "Subject confirmed alive via dark web activity post-silence",
      "category": "SubjectStatus",
      "confidence": 0.72,
      "source_count": 2
    },
    {
      "title": "Encrypted communication directed at specific recipient (protagonist)",
      "category": "Communication",
      "confidence": 0.70,
      "source_count": 1
    },
    {
      "title": "Geolocation narrowed to Marseille / southern France",
      "category": "Location",
      "confidence": 0.85,
      "source_count": 6
    },
    {
      "title": "PHANTOM MERCY shell companies linked via shared registration address",
      "category": "ThreatInfrastructure",
      "confidence": 0.95,
      "source_count": 2
    },
    {
      "title": "GCAF platform access being sold on dark web marketplace",
      "category": "ThreatActivity",
      "confidence": 0.82,
      "source_count": 1
    },
    {
      "title": "Subject OPSEC compromised by GCAF organizational social media",
      "category": "SecurityRisk",
      "confidence": 0.88,
      "source_count": 4
    }
  ],
  "recommendations": [
    "Decrypt PrivateBin paste using protagonist's PGP key -- may contain Clara's current coordinates",
    "Monitor nightingale_42 activity on Dread for additional communications",
    "Assess risk of GCAF social media exposure to Clara's safety",
    "Share PHANTOM MERCY shell company intelligence via ADAPT Mesh (TLP:AMBER)",
    "DO NOT contact GCAF directly -- organization may be compromised",
    "Establish alternative communication channel for Clara via dead-drop protocol"
  ],
  "generated_at": "2026-02-18T12:00:00Z"
}
```

---

## 13.12 Ethical Boundaries: What I Will and Won't Do

I want to be clear about something. Playseat includes dark web monitoring capabilities, but with strict ethical guardrails. Even when the person I'm looking for is someone I love, the rules don't change.

**What I'm doing:**
- Monitoring dark web forums for Clara's communications (passive collection)
- Searching public social media for location indicators
- Analyzing WHOIS and DNS records for PHANTOM MERCY infrastructure
- Cross-referencing public records and news media
- Building relationship graphs from open sources

**What I'm NOT doing:**
- Accessing GCAF's internal systems (even though I could -- the marketplace listing proves they're compromised)
- Creating fake accounts to engage with nightingale_42
- Purchasing the GCAF access listing on AlphaBay's successor
- Deanonymizing Tor users (that's someone else's job, and it would endanger Clara)
- Contacting Clara through any channel that PHANTOM MERCY might be monitoring

The defensive intelligence posture means I observe, collect, analyze, and defend. I don't go on offense against PHANTOM MERCY's network. Not yet. Not until I know Clara is safe.

---

## 13.13 Advanced Entity Resolution: Finding Patterns Across Sources

```sql
-- Entity resolution: find entities that appear across multiple sources
-- with different names but matching identifiers
SELECT
    e1.canonical_name AS entity_1,
    e2.canonical_name AS entity_2,
    e1.entity_type,
    e1.confidence AS conf_1,
    e2.confidence AS conf_2,
    (
        SELECT COUNT(*)
        FROM jsonb_array_elements_text(e1.identifiers) AS id1
        WHERE id1 IN (
            SELECT jsonb_array_elements_text(e2.identifiers)
        )
    ) AS shared_identifiers,
    jsonb_array_length(e1.identifiers) AS total_ids_1,
    jsonb_array_length(e2.identifiers) AS total_ids_2
FROM osint_entities e1
JOIN osint_entities e2
    ON e1.id < e2.id
    AND e1.entity_type = e2.entity_type
WHERE (
    SELECT COUNT(*)
    FROM jsonb_array_elements_text(e1.identifiers) AS id1
    WHERE id1 IN (
        SELECT jsonb_array_elements_text(e2.identifiers)
    )
) > 0
ORDER BY shared_identifiers DESC;
```

The result I'm looking for: Clara Dubois (entity) and nightingale_42 (entity) sharing identifiers. The writing style analysis, the PGP key linkage, the timing of posts relative to Clara's silence -- all of these are identifiers that the entity resolver uses to compute the 0.72 confidence score linking these two entities.

0.72 isn't certainty. But combined with the "cathedrals from data" reference in the PrivateBin paste -- which is something only Clara and I would know -- my personal confidence is higher than any algorithm can compute.

She's alive. She's in southern France. She's trying to reach me.

---

## 13.14 Available OSINT Sources

```bash
curl -s "http://localhost:3000/api/v1/osint/sources" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
[
  { "source_type": "SocialMedia", "name": "Social Media" },
  { "source_type": "DomainWhois", "name": "Domain WHOIS" },
  { "source_type": "DnsRecords", "name": "DNS Records" },
  { "source_type": "CertificateTransparency", "name": "Certificate Transparency" },
  { "source_type": "CodeRepository", "name": "Code Repository" },
  { "source_type": "PasteSite", "name": "Paste Site" },
  { "source_type": "DarkWebForum", "name": "Dark Web Forum" },
  { "source_type": "PublicRecords", "name": "Public Records" },
  { "source_type": "JobPostings", "name": "Job Postings" },
  { "source_type": "NewsMedia", "name": "News Media" },
  { "source_type": "AcademicPapers", "name": "Academic Papers" },
  { "source_type": "SatelliteImagery", "name": "Satellite Imagery" },
  { "source_type": "BreachDatabases", "name": "Breach Databases" },
  { "source_type": "MobileAppStore", "name": "Mobile App Store" }
]
```

14 source types. I used 10 of them to find Clara's trail. The power isn't in any single source -- it's in the correlation across all of them. A social media post alone tells you nothing. A social media post correlated with a dark web timestamp, a WHOIS record, and a geo-tagged photo tells you a story.

---

## 13.15 What Happens Next

**2026-02-18T12:30:00Z -- My apartment. Standing at the window. Thinking.**

I have her trail. Marseille. Southern France. Alive as of February 15th. Trying to communicate with me through channels that PHANTOM MERCY can't monitor.

The PrivateBin paste is still there -- it expires on February 22nd. Four days from now. I need to decrypt it. The coordinates inside might tell me exactly where she is. Or they might tell me where to meet her. Or they might tell me where the next piece of evidence is hidden.

But I also have the PHANTOM MERCY intelligence. The shell companies in Cyprus. The five CT-logged subdomains. The marketplace listing selling GCAF access. The financial SPOF. This is actionable intelligence that could shut down a child trafficking network.

I can't do both at once. I can't find Clara and take down PHANTOM MERCY simultaneously. Not alone.

Which is why the next chapter matters so much. Zero Trust -- trust no one, verify everything. Because if PHANTOM MERCY has insiders everywhere, then I need to be absolutely certain about every piece of intelligence, every communication, every person I trust.

Except Clara. She's the one person I trust completely. And I'm going to find her.

---

## 13.16 Lessons from the Field

**1. Start with infrastructure, end with people.** Domains, IPs, and certificates are facts. They don't lie. Start there and let the infrastructure lead you to the person -- whether that person is a threat actor or a missing ally.

**2. CT logs are the OSINT analyst's best friend.** PHANTOM MERCY's five subdomains were all logged. They didn't intend for `ops.pm-network.example` to be publicly discoverable. CT logs made it discoverable.

**3. Social media from organizations is an OPSEC risk for individuals.** Clara had perfect personal OPSEC. GCAF's social media team destroyed it by posting geo-tagged photos and naming her in newsletters. If you're running a deep-cover operation, control the organization's comms team.

**4. Writing style is a biometric.** Clara's mathematical metaphors, rhetorical questions, and sentence structure are as unique as a fingerprint. On the dark web, where everyone is anonymous, writing style is how you identify individuals.

**5. Attribution confidence is a number, not a word.** nightingale_42 is Clara with 0.72 algorithmic confidence and near-certainty personal confidence. Report both. The algorithm doesn't know about "cathedrals from data." The human does.

---

## 13.17 Quick Reference

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create profile | `/api/v1/osint/profiles` | POST |
| List profiles | `/api/v1/osint/profiles` | GET |
| Get profile | `/api/v1/osint/profiles/{id}` | GET |
| List sources | `/api/v1/osint/sources` | GET |
| Search sources | `/api/v1/osint/search` | POST |
| List entities | `/api/v1/osint/entities` | GET |
| Resolve entities | `/api/v1/osint/entities/resolve` | POST |
| Get exposure score | `/api/v1/osint/score/{id}` | GET |
| Get graph | `/api/v1/osint/graph/{id}` | GET |
| Build graph | `/api/v1/osint/graph/build` | POST |
| Get report | `/api/v1/osint/reports/{id}` | GET |
| Generate report | `/api/v1/osint/reports/generate` | POST |

---

*Next chapter: Zero Trust Implementation -- because PHANTOM MERCY has insiders everywhere, and the only person I trust completely is the one I'm trying to find.*

---

`© 2026 Playseat — All Rights Reserved | Defensive Intelligence Through ADAPT`
