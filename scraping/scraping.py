import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import ast

# Funktion til at scrape stemmeinformationer fra en given URL
def scrape_vote_info(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find elementerne med de relevante klasser
        header = soup.find('div', class_="tingdok__caseinfotopspot-a__container")
        details = soup.find('div', class_='tingdok__caseinfospot-a__container')
        
        if details and header:
            try:
                # Find de relevante child-elementer
                date = details.find_all(recursive=False)[1]
                votes = details.find_all(recursive=False)[-1]
                section = details.find_all(recursive=False)[8]
                explanation = details.find_all(recursive=False)[11]
                # Organiser informationen i et dictionary
                vote_info = {
                    'ID': header.find_all(recursive=False)[0].get_text(strip=True)[:5].replace(' ', '') ,
                    'title': header.find_all(recursive=False)[0].get_text(strip=True)[5:],
                    'who': header.find_all(recursive=False)[3].get_text(strip=True),
                    'date': date.get_text(strip=True),
                    'section': section.get_text(strip=True),
                    'explanation': explanation.get_text(strip=True),
                    'votes': parse_votes(votes.get_text(strip=True))
                }
                return vote_info
            except (ValueError, IndexError) as e:
                print(f"Error parsing details for URL {url}: {e}")
                return None
        else:
            print(f"Details or header not found for URL {url}")
            return None
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None

# Funktion til at parse stemmeinformationer
def parse_votes(votes_text):
    votes_lines = votes_text.split('\n')
    votes_dict = {
        'status': votes_lines[0],
        'for': parse_vote_line(votes_lines[1]),
        'against': parse_vote_line(votes_lines[2]),
        'abstained': parse_vote_line(votes_lines[3]) if len(votes_lines) > 3 and 'hverken' in votes_lines[3] else {'count': 0, 'parties': []}
    }
    return votes_dict

# Funktion til at parse en enkelt stemmelinje
def parse_vote_line(line):
    parts = line.split(' ')
    try:
        count = int(parts[2])
    except ValueError:
        count = 0
    parties = ' '.join(parts[3:]).strip('()')
    return {'count': count, 'parties': [party.strip() for party in parties.split(',') if party.strip()]}

def get_links():
    # URL til den side, du vil scrape
    root = "https://www.ft.dk/dokumenter/dokumentlister/lovforslag?session=20241&pageSize=200&totalNumberOfRecords=257"
    response = requests.get(root)

    # Tjek om forespørgslen var succesfuld
    if response.status_code == 200:
        # Parse HTML indholdet med BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
    links = set()  # Brug en set for at sikre unikke links
    for td in soup.find_all('td', class_='column-documents'):
        a_tag = td.find('a', class_='column-documents__link')
        if a_tag and 'href' in a_tag.attrs:
            href = a_tag['href']
            full_url = "https://www.ft.dk" + href  # Konstruer den fulde URL
            links.add(full_url)
    unique_links = list(links)  # Konverter set til liste
    print("Found unique links:", unique_links)  # Debugging statement
    return unique_links

def run():
    all_vote_info = {}
    urls = get_links() 
    print(len(urls))
    for url in urls:
        vote_info = scrape_vote_info(url)
        if isinstance(vote_info, dict):
            # Brug lovforslags ID som key og tilføj til overordnet dictionary
            proposal_id = vote_info['ID']
            all_vote_info[proposal_id] = vote_info
    plot_votes(all_vote_info)     

# Funktion til at samle data og lave et plot
def plot_votes(all_vote_info):
    section_votes = {}
    
    for proposal_id, info in all_vote_info.items():
        section = info['section']
        if "Ministerområde" not in section:
            continue  # Skip sektioner, der ikke indeholder "Ministerområde"
        votes = info['votes']
        
        if section not in section_votes:
            section_votes[section] = {'for': {}, 'against': {}}
        
        for party in votes['for']['parties']:
            if party not in section_votes[section]['for']:
                section_votes[section]['for'][party] = 0
            section_votes[section]['for'][party] += 1
        
        for party in votes['against']['parties']:
            if party not in section_votes[section]['against']:
                section_votes[section]['against'][party] = 0
            section_votes[section]['against'][party] += 1
    
     # Print data
    print("Section Votes:")
    with open("section_votes.txt", "w") as file:
        for section, votes in section_votes.items():
            print(f"Section: {section}")
            file.write(f"Section: {section}\n")
            print(f"  For: {votes['for']}")
            file.write(f"  For: {votes['for']}\n")
            print(f"  Against: {votes['against']}")
            file.write(f"  Against: {votes['against']}\n")
    # Plot data
    sections = list(section_votes.keys())
    for_votes = {section: sum(section_votes[section]['for'].values()) for section in sections}
    against_votes = {section: sum(section_votes[section]['against'].values()) for section in sections}
    
    x = range(len(sections))
    
    plt.figure(figsize=(10, 5))
    plt.bar(x, for_votes.values(), width=0.4, label='For', align='center')
    plt.bar(x, against_votes.values(), width=0.4, label='Against', align='edge')
    
    plt.xlabel('Sections')
    plt.ylabel('Votes')
    plt.title('Votes by Sections')
    plt.xticks(x, sections, rotation=45)  # Ændret rotation til 45 grader for skrå tekst
    plt.legend()
    plt.tight_layout()
    plt.savefig('first.png')

# Funktion til at læse data fra filen
def read_data_from_file(filename):
    section_votes = {}
    with open(filename, "r") as file:
        lines = file.readlines()
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("Section:"):
                current_section = line.replace("Section: ", "")
                section_votes[current_section] = {'for': {}, 'against': {}}
            elif line.startswith("For:"):
                votes_for = ast.literal_eval(line.replace("For: ", ""))
                section_votes[current_section]['for'] = votes_for
            elif line.startswith("Against:"):
                votes_against = ast.literal_eval(line.replace("Against: ", ""))
                section_votes[current_section]['against'] = votes_against
    return section_votes

# Funktion til at lave plots baseret på dataen
def plot_votes_detailed(section_votes):
    
    for section, votes in section_votes.items():
        parties = list(set(list(votes['for'].keys()) + list(votes['against'].keys())))
        for_counts = [votes['for'].get(party, 0) for party in parties]
        against_counts = [votes['against'].get(party, 0) for party in parties]
        
        x = range(len(parties))
        
        plt.figure(figsize=(10, 5))
        plt.bar(x, for_counts, width=0.4, label='For', align='center')
        plt.bar(x, against_counts, width=0.4, label='Against', align='edge')
        
        plt.xlabel('Parties')
        plt.ylabel('Votes')
        plt.title(f'Votes by Parties for {section}')
        plt.xticks(x, parties, rotation=45)
        plt.legend()
        plt.tight_layout()
        title = section.replace(":", "_") + ".png"
        print(title)
        plt.savefig(title)

run()
# Læs data fra filen
section_votes = read_data_from_file("section_votes.txt")

# Lav plots baseret på dataen
plot_votes_detailed(section_votes)