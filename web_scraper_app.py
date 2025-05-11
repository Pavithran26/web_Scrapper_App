import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Interactive Web Scraper",
    page_icon="🌐",
    layout="wide"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main {
        max-width: 1000px;
        padding: 2rem;
    }
    .stTextInput input {
        font-size: 16px !important;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .result-box {
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 1rem;
        margin-top: 1rem;
        background-color: #f9f9f9;
    }
    .footer {
        margin-top: 2rem;
        text-align: center;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.title("🌐 Interactive Web Scraper")
st.markdown("Extract content from any website with this easy-to-use tool.")

# Sidebar with options
with st.sidebar:
    st.header("Options")
    extraction_choice = st.radio(
        "What would you like to extract?",
        ("Paragraphs", "Headings", "Links", "Tables", "Images")
    )
    
    st.markdown("---")
    st.markdown("**Note:**")
    st.markdown("- Some websites may block scraping attempts")
    st.markdown("- Always respect robots.txt and terms of service")
    st.markdown("- For JavaScript-heavy sites, consider using browser automation")

# Main content area
url = st.text_input("Enter website URL:", placeholder="https://example.com")

if st.button("Scrape Website"):
    if not url:
        st.warning("Please enter a URL")
    else:
        # Validate URL
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                st.error("Invalid URL format. Please include http:// or https://")
                st.stop()
        except ValueError:
            st.error("Invalid URL format")
            st.stop()
        
        # Show loading spinner
        with st.spinner(f"Fetching data from {url}..."):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                html = response.text
            except requests.RequestException as e:
                st.error(f"Error fetching the website: {e}")
                st.stop()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Display results based on user choice
        st.success("Successfully fetched website content!")
        st.markdown(f"### Extracted {extraction_choice.lower()} from {url}")
        
        with st.expander("View Raw HTML (Advanced)", expanded=False):
            st.code(html[:2000] + "..." if len(html) > 2000 else html)
        
        result_container = st.container()
        
        if extraction_choice == "Paragraphs":
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
            if paragraphs:
                with result_container:
                    st.markdown("#### Paragraphs Found:")
                    for i, para in enumerate(paragraphs[:50]):  # Limit to first 50 paragraphs
                        st.markdown(f"**Paragraph {i+1}:**")
                        st.markdown(f'<div class="result-box">{para}</div>', unsafe_allow_html=True)
            else:
                st.warning("No paragraphs found on this page.")
        
        elif extraction_choice == "Headings":
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if headings:
                with result_container:
                    st.markdown("#### Headings Structure:")
                    for heading in headings:
                        level = int(heading.name[1])
                        st.markdown(f"{'#' * level} {heading.get_text().strip()}")
            else:
                st.warning("No headings found on this page.")
        
        elif extraction_choice == "Links":
            links = soup.find_all('a', href=True)
            if links:
                external_links = []
                internal_links = []
                for link in links:
                    href = link['href']
                    if href.startswith('http'):
                        if urlparse(href).netloc == urlparse(url).netloc:
                            internal_links.append({"URL": href, "Text": link.get_text().strip(), "Type": "Internal"})
                        else:
                            external_links.append({"URL": href, "Text": link.get_text().strip(), "Type": "External"})
                
                with result_container:
                    st.markdown(f"Found {len(external_links)} external links and {len(internal_links)} internal links")
                    
                    tab1, tab2 = st.tabs(["External Links", "Internal Links"])
                    
                    with tab1:
                        if external_links:
                            st.dataframe(pd.DataFrame(external_links))
                        else:
                            st.info("No external links found")
                    
                    with tab2:
                        if internal_links:
                            st.dataframe(pd.DataFrame(internal_links))
                        else:
                            st.info("No internal links found")
            else:
                st.warning("No links found on this page.")
        
        elif extraction_choice == "Tables":
            tables = soup.find_all('table')
            if tables:
                with result_container:
                    st.markdown(f"Found {len(tables)} tables")
                    for i, table in enumerate(tables[:3]):  # Limit to first 3 tables
                        st.markdown(f"#### Table {i+1}")
                        try:
                            df = pd.read_html(str(table))[0]
                            st.dataframe(df)
                        except:
                            st.warning("Could not parse this table")
                        st.markdown("---")
            else:
                st.warning("No tables found on this page.")
        
        elif extraction_choice == "Images":
            images = soup.find_all('img')
            if images:
                with result_container:
                    st.markdown(f"Found {len(images)} images")
                    cols = st.columns(3)
                    for i, img in enumerate(images[:9]):  # Limit to first 9 images
                        src = img.get('src', '')
                        alt = img.get('alt', 'No alt text')
                        if src:
                            if not src.startswith('http'):
                                # Handle relative URLs
                                if src.startswith('/'):
                                    src = f"{urlparse(url).scheme}://{urlparse(url).netloc}{src}"
                                else:
                                    src = f"{url}/{'/' if not url.endswith('/') else ''}{src}"
                            cols[i%3].image(src, caption=alt[:50] + "..." if len(alt) > 50 else alt, use_column_width=True)
            else:
                st.warning("No images found on this page.")

# Footer
st.markdown("---")
st.markdown('<div class="footer">Web Scraper App - Use responsibly and respect website terms of service</div>', unsafe_allow_html=True)