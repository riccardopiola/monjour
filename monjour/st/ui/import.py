import streamlit as st
import datetime as dt
from monjour.st import StApp
from monjour.core.common import DateRange

import monjour.core.log as log

st_app = StApp(st.session_state.project_dir)

st.write('### Import a new file')
# Create a dropdown menu
accounts = st_app.app.accounts
importers = st_app.list_all_importers()

# Account selection
(c1, c2) = st.columns(2)
account_id = c1.selectbox('Account', importers.keys(),
                        format_func=lambda id: f"{accounts[id].id} [{accounts[id].PROVIDER_ID}]")
if account_id:
    # Importer selection
    account = accounts[account_id]
    all_importers = sorted(importers[account_id], key=lambda imp: imp.id == account.importer.info.id, reverse=True)
    importer_id = c2.selectbox('Importer', all_importers,
                               format_func=lambda imp: imp.id)
    importer = account.set_importer(importer_id.id)

    # File picker
    if file := st.file_uploader('File'):
        # TODO: Check if the importer can handle the file

        # Try to infer date range from the file
        inferred_end = dt.datetime.now()
        inferred_start = inferred_end - dt.timedelta(days=30)
        try:
            if (date_range := importer.try_infer_daterange(file, file.name)) is not None:
                inferred_start = date_range.start
                inferred_end = date_range.end
                st.info(f"""The date range was inferred automatically. Adjust it if necessary.""")
        except NotImplementedError:
            st.info(f"""The selected importer does not support inferring the date range from the filename.
            Please select the date range manually.""")
        except Exception as e:
            msg = f"Error while trying to automatically infer date range: {e}"
            st.warning(msg)
            log.warning(msg)
        finally:
            file.seek(0)

        # Date range selection controls return a tuple of two datetime objects
        date_range = st.date_input('Date range',
            value=(inferred_start, inferred_end),
            max_value=dt.datetime.now(), # not sure if this is necessary
        )

        # Submit button
        if st.button('Import', type='primary'):
            with st_app.app.interactive as iapp:
                import_ctx =iapp.archive_file(
                    account_id,
                    file,
                    file.name,
                    date_range=DateRange(
                        dt.datetime.combine(date_range[0], dt.time.min), # type: ignore
                        dt.datetime.combine(date_range[1], dt.time.max) # type: ignore
                    ),
                )
            st.success(f'File "{file.name}" imported successfully.')
            import_ctx.st_show_diagnostics()
