import os
import base64
import aiohttp
import asyncio

async def create_onedrive_directdownload(onedrive_link):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_string = data_bytes64.decode('utf-8').replace('/', '_').replace('+', '-').rstrip("=")
    result_url = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_string}/root"
    return result_url

async def get_filename_from_metadata(metadata):
    if 'name' in metadata:
        return metadata['name']
    return 'DownloadedFile.xlsm'

async def download_file_fake(direct_download_url):
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
                            content = await content_response.read()
                            # Save the content to a local file with the suggested filename
                            with open(suggested_filename, 'wb') as file:
                                file.write(content)
                            absolute_path = os.path.abspath(suggested_filename)
                            print(f'Download successful. File saved as: {absolute_path}')
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
    direct_download_url = await create_onedrive_directdownload('https://1drv.ms/x/s!Ak0dKSJpYkQFhDLofq7_zWkxYG6L?e=Jlqhsf')

    # Run the event loop for the async function
    absolute_path = await download_file_fake(direct_download_url)

    # Now you can use the 'absolute_path' variable in other methods or export it as needed
    print(f'Absolute path outside download_file_fake: {absolute_path}')

# Run the event loop to execute the asynchronous code
asyncio.run(main())
