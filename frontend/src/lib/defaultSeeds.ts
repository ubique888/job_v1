export interface DefaultSeed {
  company: string;
  provider: "greenhouse" | "lever";
  token: string;
  category: string;
}

export const CATEGORIES = [
  "Big Tech",
  "SaaS",
  "Data & Dev Tools",
  "Cybersecurity",
  "Consumer & Streaming",
  "Fintech",
  "Consulting",
] as const;

export const DEFAULT_SEEDS: DefaultSeed[] = [
  // Big Tech
  { company: "Netflix", provider: "lever", token: "netflix", category: "Big Tech" },

  // SaaS
  { company: "Adobe", provider: "lever", token: "adobe", category: "SaaS" },
  { company: "Shopify", provider: "lever", token: "shopify", category: "SaaS" },
  { company: "Twilio", provider: "greenhouse", token: "twilio", category: "SaaS" },
  { company: "HubSpot", provider: "greenhouse", token: "hubspot", category: "SaaS" },

  // Data & Dev Tools
  { company: "Databricks", provider: "greenhouse", token: "databricks", category: "Data & Dev Tools" },
  { company: "MongoDB", provider: "greenhouse", token: "mongodb", category: "Data & Dev Tools" },
  { company: "Datadog", provider: "greenhouse", token: "datadog", category: "Data & Dev Tools" },
  { company: "Cloudflare", provider: "greenhouse", token: "cloudflare", category: "Data & Dev Tools" },

  // Cybersecurity
  { company: "Okta", provider: "greenhouse", token: "okta", category: "Cybersecurity" },
  { company: "Zscaler", provider: "greenhouse", token: "zscaler", category: "Cybersecurity" },
  { company: "Splunk", provider: "greenhouse", token: "splunk", category: "Cybersecurity" },
  { company: "Wiz", provider: "greenhouse", token: "wizinc", category: "Cybersecurity" },
  { company: "Rubrik", provider: "greenhouse", token: "rubrik", category: "Cybersecurity" },

  // Consumer & Streaming
  { company: "Airbnb", provider: "greenhouse", token: "airbnb", category: "Consumer & Streaming" },
  { company: "Pinterest", provider: "greenhouse", token: "pinterest", category: "Consumer & Streaming" },
  { company: "Roku", provider: "greenhouse", token: "roku", category: "Consumer & Streaming" },
  { company: "Spotify", provider: "lever", token: "spotify", category: "Consumer & Streaming" },

  // Fintech
  { company: "Stripe", provider: "greenhouse", token: "stripe", category: "Fintech" },
  { company: "Block (Square)", provider: "greenhouse", token: "block", category: "Fintech" },
  { company: "Coinbase", provider: "greenhouse", token: "coinbase", category: "Fintech" },
  { company: "Robinhood", provider: "greenhouse", token: "robinhood", category: "Fintech" },

  // Consulting
  { company: "Oliver Wyman", provider: "lever", token: "oliverwyman", category: "Consulting" },
  { company: "AlixPartners", provider: "greenhouse", token: "alixpartners", category: "Consulting" },
  { company: "Capco", provider: "greenhouse", token: "capco", category: "Consulting" },
  { company: "BearingPoint", provider: "greenhouse", token: "bearingpoint", category: "Consulting" },
  { company: "Thoughtworks", provider: "greenhouse", token: "thoughtworks", category: "Consulting" },
  { company: "TCS", provider: "greenhouse", token: "tcs", category: "Consulting" },
  { company: "Charles River Associates", provider: "greenhouse", token: "charlesriverassociates", category: "Consulting" },
  { company: "The Brattle Group", provider: "greenhouse", token: "thebrattlegroup", category: "Consulting" },
  { company: "Compass Lexecon", provider: "lever", token: "compasslexecon", category: "Consulting" },
  { company: "Avalere Health", provider: "lever", token: "avalerehealth", category: "Consulting" },
  { company: "ClearView Healthcare Partners", provider: "greenhouse", token: "clearviewhealthcarepartners", category: "Consulting" },
];

export function getBoardUrl(seed: DefaultSeed): string {
  if (seed.provider === "greenhouse") {
    return `https://boards.greenhouse.io/${seed.token}`;
  }
  return `https://jobs.lever.co/${seed.token}`;
}
