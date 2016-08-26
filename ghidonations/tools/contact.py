def merge_contacts(c1_key, c2_key):
    c1 = c1_key.get()
    c2 = c2_key.get()

    # Ff contact 2 doesn't have an value and contact 1 does,
    # replace c2's value with c1's

    combined_emails = c2.email + c1.email

    try:
        combined_emails.remove("")
    except Exception:
        pass

    c2.email = combined_emails

    if c2.phone == "" and c1.phone != "":
        c2.phone = c1.phone

    if c2.notes == "" or c2.notes == "None" and c1.notes != "":
        c2.notes = c1.notes

    if c2.address == ['', '', '', ''] and c1.address != ['', '', '', '']:
        c2.address = c1.address

    # Merge the donations from c1 all to c2
    for d in c1.data.all_donations:
        d.contact = c2_key
        d.put()

    # Save c2
    c2.put()

    # Finally, delete c1
    c1.key.delete()