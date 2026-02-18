export type PackColorVariant = 'orange' | 'pink' | 'green' | 'blue' | 'gray';

export interface FeaturedPackConfig {
  id: string;
  title: string;
  city: string;
  state: string;
  country: string;
  county?: string;
  niche: string;
  query: string;
  limit: number;
  color: PackColorVariant;
  product_type?: 'basic_pack' | 'enriched_pack';
}

export const FEATURED_PACKS: FeaturedPackConfig[] = [
  {
    id: 'restaurants_boca_raton_fl',
    title: 'Restaurants • Boca Raton, FL',
    city: 'Boca Raton',
    state: 'Florida',
    country: 'USA',
    county: 'Palm Beach County',
    niche: 'restaurants',
    query: 'restaurants in Boca Raton, FL',
    limit: 20,
    color: 'orange',
  },
  {
    id: 'nail_salons_miami_fl',
    title: 'Nail Salons • Miami, FL',
    city: 'Miami',
    state: 'Florida',
    country: 'USA',
    county: 'Miami-Dade County',
    niche: 'nail salons',
    query: 'nail salons in Miami, FL',
    limit: 20,
    color: 'pink',
  },
  {
    id: 'gyms_tampa_fl',
    title: 'Gyms • Tampa, FL',
    city: 'Tampa',
    state: 'Florida',
    country: 'USA',
    county: 'Hillsborough County',
    niche: 'gyms',
    query: 'gyms in Tampa, FL',
    limit: 20,
    color: 'green',
  },
  {
    id: 'real_estate_agencies_dallas_tx',
    title: 'Real Estate Agencies • Dallas, TX',
    city: 'Dallas',
    state: 'Texas',
    country: 'USA',
    county: 'Dallas County',
    niche: 'real estate agencies',
    query: 'real estate agencies in Dallas, TX',
    limit: 20,
    color: 'blue',
  },
  {
    id: 'hair_salons_barber_shops_fort_lauderdale_fl',
    title: 'Hair Salons & Barbers • Fort Lauderdale, FL',
    city: 'Fort Lauderdale',
    state: 'Florida',
    country: 'USA',
    county: 'Broward County',
    niche: 'hair salons',
    query: 'hair salons and barber shops in Fort Lauderdale, FL',
    limit: 20,
    color: 'pink',
  },
  {
    id: 'auto_repair_shops_atlanta_ga',
    title: 'Auto Repair Shops • Atlanta, GA',
    city: 'Atlanta',
    state: 'Georgia',
    country: 'USA',
    county: 'Fulton County',
    niche: 'auto repair shops',
    query: 'auto repair shops in Atlanta, GA',
    limit: 20,
    color: 'gray',
  },
  {
    id: 'cleaning_services_charlotte_nc',
    title: 'Cleaning Services • Charlotte, NC',
    city: 'Charlotte',
    state: 'North Carolina',
    country: 'USA',
    county: 'Mecklenburg County',
    niche: 'cleaning services',
    query: 'cleaning services in Charlotte, NC',
    limit: 20,
    color: 'gray',
  },
  {
    id: 'dentists_orlando_fl',
    title: 'Dentists • Orlando, FL',
    city: 'Orlando',
    state: 'Florida',
    country: 'USA',
    county: 'Orange County',
    niche: 'dentists',
    query: 'dentists in Orlando, FL',
    limit: 20,
    color: 'blue',
  },
  {
    id: 'daycares_preschools_austin_tx',
    title: 'Daycares & Preschools • Austin, TX',
    city: 'Austin',
    state: 'Texas',
    country: 'USA',
    county: 'Travis County',
    niche: 'daycares preschools',
    query: 'daycares and preschools in Austin, TX',
    limit: 20,
    color: 'green',
  },
  {
    id: 'tour_companies_kingston_jamaica',
    title: 'Tour Companies • Kingston, Jamaica',
    city: 'Kingston',
    state: 'Kingston Parish',
    country: 'Jamaica',
    county: 'Kingston Parish',
    niche: 'tour companies',
    query: 'tour companies in Kingston, Jamaica',
    limit: 20,
    color: 'orange',
  },
];
