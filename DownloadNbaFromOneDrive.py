import os
import base64
import aiohttp
import asyncio
from dotenv import load_dotenv, set_key
from tqdm import tqdm

load_dotenv()

ONEDRIVE_EXCEL_NBA_PATH = os.getenv("ONEDRIVE_EXCEL_NBA_PATH")

async def create_onedrive_directdownload(onedrive_link):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_string = data_bytes64.decode('utf-8').replace('/', '_').replace('+', '-').rstrip("=")
    result_url = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_string}/root"
    return result_url

async def get_filename_from_metadata(metadata):
    if 'name' in metadata:
        return metadata['name']
    return 'DownloadedFile.xlsm'

async def download_file_fake(direct_download_url, progress_bar):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(direct_download_url) as response:
                # Check if the request was successful (status code 200)
                if response.status == 200:
                    # Extract the filename from the metadata
                    metadata = await response.json()
                    suggested_filename = await get_filename_from_metadata(metadata)                    

                    # Get the actual content download URL
                    download_url = metadata.get('@content.downloadUrl')

                    if download_url:
                        # Download the actual content using the provided download URL
                        async with session.get(download_url) as content_response:
                            content_length = int(content_response.headers.get('Content-Length', 0))
                            progress_bar.total = content_length

                            # Save the content to a local file with the suggested filename
                            with tqdm.wrapattr(open(suggested_filename, 'wb'), 'write', miniters=1,
                                               total=content_length, desc=f'Downloading {suggested_filename}') as file:
                                async for chunk in content_response.content.iter_any():
                                    file.write(chunk)

                            absolute_path = os.path.abspath(suggested_filename)
                            # Set the absolute path in the .env file                            
                            set_key('.env', 'LOCAL_EXCEL_NBA_PATH', absolute_path, quote_mode="never")

                            print(f'\nDownload successful. File saved as: {absolute_path}')
                            return absolute_path
                    else:
                        print('Error: Download URL not found in metadata.')

                else:
                    print(f'Failed to download the file. HTTP Status Code: {response.status}')
                    print(f'Error Response: {await response.text()}')

    except Exception as e:
        print(f'An error occurred: {e}')

async def main():
    # Generate the direct download URL
    direct_download_url = await create_onedrive_directdownload(ONEDRIVE_EXCEL_NBA_PATH)

    # Run the event loop for the async function
    with tqdm() as progress_bar:
        absolute_path = await download_file_fake(direct_download_url, progress_bar)

    # Now you can use the 'absolute_path' variable in other methods or export it as needed
    print(f'Absolute path outside download_file_fake: {absolute_path}')

# Run the event loop to execute the asynchronous code
asyncio.run(main())
