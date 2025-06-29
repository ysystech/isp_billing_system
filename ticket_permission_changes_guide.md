# Ticket Permission Changes Implementation Guide

## Changes Implemented

1. **Permission Structure Updates**:
   - Removed: `assign_ticket` (Technician assignment is now part of `edit_ticket`)
   - Added: `edit_ticket` (General permission to edit ticket information)
   - Modified: `change_ticket_status` (Now dedicated to the status control outside the edit form)

2. **Code Changes**:
   - Updated permission mappings in `map_permissions_to_categories.py`
   - Updated view decorators in `views.py` to use new permissions
   - Added a status update modal in the ticket detail template
   - Updated template permission checks

## How to Apply the Changes

### Step 1: Run the setup command

```bash
make manage ARGS="setup_edit_ticket_permission"
```

This will:
- Create the new `edit_ticket` permission in the database
- Update the permission mappings
- Provide confirmation when complete

### Step 2: Restart your development server

```bash
make stop
make start
```

### Step 3: Update your roles

1. Go to http://localhost:8000/roles/
2. For each role that needs ticket management abilities:
   - Click on the role
   - Go to the "Permissions" tab
   - Update the Support Tickets permissions according to your requirements
   - Make sure to assign `edit_ticket` to roles that need general ticket editing
   - Make sure to assign `change_ticket_status` to roles that need to change ticket status

### Step 4: Test the changes

1. Log in as a user with appropriate permissions
2. Go to http://localhost:8000/tickets/
3. Test the following:
   - Users with `edit_ticket` can edit ticket details
   - Users with `change_ticket_status` can change status via the modal
   - Users without these permissions don't see the respective buttons

## New Permission Behavior

- **Edit Ticket**: Users can edit all ticket information including assignment, but not status (unless they also have the status permission)
- **Change Ticket Status**: Users can change the ticket status through a dedicated control, even if they can't edit other ticket details

## Notes

- The technician assignment is now part of the general ticket editing functionality
- Status changes are tracked in the ticket comments automatically
- Both general editing and status-only changes are available based on permissions