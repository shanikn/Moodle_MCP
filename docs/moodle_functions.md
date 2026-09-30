# Moodle API functions available to the student token

Source: `core_webservice_get_site_info` on https://moodle.runi.ac.il/2026 (Moodle 4.5.14 (Build: 20260914)).
443 functions in 73 groups. **(planned)** = used by a planned MCP tool.

Descriptions come from each function's `description` in `<component>/db/services.php` on the
[MOODLE_405_STABLE branch](https://github.com/moodle/moodle/tree/MOODLE_405_STABLE);
parameters and return fields are in the matching `classes/external/` file.
Third-party plugins ([mod_checklist](https://github.com/davosmith/moodle-checklist), [mod_choicegroup](https://github.com/ndunand/moodle-mod_choicegroup), [mod_questionnaire](https://github.com/PoetOS/moodle-mod_questionnaire)) are described from their own repos.

## Groups

- [aiplacement_courseassist](#aiplacement_courseassist) (1)
- [aiplacement_editor](#aiplacement_editor) (2)
- [block_recentlyaccesseditems](#block_recentlyaccesseditems) (1)
- [block_starredcourses](#block_starredcourses) (1)
- [core_ai](#core_ai) (2)
- [core_badges](#core_badges) (3)
- [core_block](#core_block) (3)
- [core_blog](#core_blog) (7)
- [core_calendar](#core_calendar) (15)
- [core_comment](#core_comment) (3)
- [core_competency](#core_competency) (9)
- [core_completion](#core_completion) (4)
- [core_course](#core_course) (16)
- [core_enrol](#core_enrol) (4)
- [core_files](#core_files) (3)
- [core_filters](#core_filters) (2)
- [core_get](#core_get) (1)
- [core_grades](#core_grades) (10)
- [core_group](#core_group) (6)
- [core_h5p](#core_h5p) (1)
- [core_message](#core_message) (41)
- [core_my](#core_my) (1)
- [core_notes](#core_notes) (4)
- [core_question](#core_question) (1)
- [core_rating](#core_rating) (2)
- [core_reportbuilder](#core_reportbuilder) (5)
- [core_search](#core_search) (4)
- [core_table](#core_table) (1)
- [core_tag](#core_tag) (5)
- [core_user](#core_user) (16)
- [core_webservice](#core_webservice) (1)
- [core_xapi](#core_xapi) (6)
- [enrol_guest](#enrol_guest) (2)
- [enrol_self](#enrol_self) (2)
- [gradereport_grader](#gradereport_grader) (1)
- [gradereport_overview](#gradereport_overview) (2)
- [gradereport_singleview](#gradereport_singleview) (1)
- [gradereport_user](#gradereport_user) (4)
- [message_airnotifier](#message_airnotifier) (4)
- [message_popup](#message_popup) (2)
- [mod_assign](#mod_assign) (24)
- [mod_bigbluebuttonbn](#mod_bigbluebuttonbn) (10)
- [mod_book](#mod_book) (2)
- [mod_chat](#mod_chat) (9)
- [mod_checklist](#mod_checklist) (1)
- [mod_choice](#mod_choice) (6)
- [mod_choicegroup](#mod_choicegroup) (4)
- [mod_data](#mod_data) (11)
- [mod_feedback](#mod_feedback) (14)
- [mod_folder](#mod_folder) (2)
- [mod_forum](#mod_forum) (17)
- [mod_glossary](#mod_glossary) (18)
- [mod_h5pactivity](#mod_h5pactivity) (7)
- [mod_imscp](#mod_imscp) (2)
- [mod_label](#mod_label) (1)
- [mod_lesson](#mod_lesson) (17)
- [mod_lti](#mod_lti) (3)
- [mod_page](#mod_page) (2)
- [mod_questionnaire](#mod_questionnaire) (1)
- [mod_quiz](#mod_quiz) (18)
- [mod_resource](#mod_resource) (2)
- [mod_scorm](#mod_scorm) (9)
- [mod_survey](#mod_survey) (4)
- [mod_url](#mod_url) (2)
- [mod_wiki](#mod_wiki) (10)
- [mod_workshop](#mod_workshop) (19)
- [report_insights](#report_insights) (3)
- [tool_analytics](#tool_analytics) (1)
- [tool_dataprivacy](#tool_dataprivacy) (5)
- [tool_lp](#tool_lp) (8)
- [tool_mobile](#tool_mobile) (8)
- [tool_moodlenet](#tool_moodlenet) (2)
- [tool_policy](#tool_policy) (2)

## aiplacement_courseassist

| Function | Description |
|---|---|
| `aiplacement_courseassist_summarise_text` | Summarise text for the Course Assistance Placement |

## aiplacement_editor

| Function | Description |
|---|---|
| `aiplacement_editor_generate_image` | Generate image for the HTML Text editor AI Placement |
| `aiplacement_editor_generate_text` | Generate text for the HTML Text editor AI Placement |

## block_recentlyaccesseditems

| Function | Description |
|---|---|
| `block_recentlyaccesseditems_get_recent_items` | List of items a user has accessed most recently. |

## block_starredcourses

| Function | Description |
|---|---|
| `block_starredcourses_get_starred_courses` | Get users starred courses. |

## core_ai

| Function | Description |
|---|---|
| `core_ai_get_policy_status` | Get a users AI policy acceptance |
| `core_ai_set_policy_status` | Set a users AI policy acceptance |

## core_badges

| Function | Description |
|---|---|
| `core_badges_get_badge` | Retrieves a badge by id. |
| `core_badges_get_user_badge_by_hash` | Returns the badge awarded to a user by hash. |
| `core_badges_get_user_badges` | Returns the list of badges awarded to a user. |

## core_block

| Function | Description |
|---|---|
| `core_block_fetch_addable_blocks` | Returns all addable blocks in a given page. |
| `core_block_get_course_blocks` | Returns blocks information for a course. |
| `core_block_get_dashboard_blocks` | Returns blocks information for the given user dashboard. |

## core_blog

| Function | Description |
|---|---|
| `core_blog_add_entry` | Creates a new blog post entry. |
| `core_blog_delete_entry` | Deletes a blog post entry. |
| `core_blog_get_access_information` | Retrieves permission information for the current user. |
| `core_blog_get_entries` | Returns blog entries. |
| `core_blog_prepare_entry_for_edition` | Prepare a draft area for editing a blog entry.. |
| `core_blog_update_entry` | Updates a blog entry. |
| `core_blog_view_entries` | Trigger the blog_entries_viewed event. |

## core_calendar

| Function | Description |
|---|---|
| `core_calendar_create_calendar_events` | Create calendar events |
| `core_calendar_delete_calendar_events` | Delete calendar events |
| `core_calendar_get_action_events_by_course` | Get calendar action events by course |
| `core_calendar_get_action_events_by_courses` | Get calendar action events by courses |
| `core_calendar_get_action_events_by_timesort` **(planned)** | Get calendar action events by tiemsort |
| `core_calendar_get_allowed_event_types` | Get the type of events a user can create in the given course. |
| `core_calendar_get_calendar_access_information` | Convenience function to retrieve some permissions/access information for the given course calendar. |
| `core_calendar_get_calendar_day_view` | Fetch the day view data for a calendar |
| `core_calendar_get_calendar_event_by_id` | Get calendar event by id |
| `core_calendar_get_calendar_events` | Get calendar events |
| `core_calendar_get_calendar_export_token` | Return the auth token required for exporting a calendar. |
| `core_calendar_get_calendar_monthly_view` | Fetch the monthly view data for a calendar |
| `core_calendar_get_calendar_upcoming_view` | Fetch the upcoming view data for a calendar |
| `core_calendar_submit_create_update_form` | Submit form data for event form |
| `core_calendar_update_event_start_day` | Update the start day (but not time) for an event. |

## core_comment

| Function | Description |
|---|---|
| `core_comment_add_comments` | Adds a comment or comments. |
| `core_comment_delete_comments` | Deletes a comment or comments. |
| `core_comment_get_comments` | Returns comments. |

## core_competency

| Function | Description |
|---|---|
| `core_competency_competency_viewed` | Log event competency viewed |
| `core_competency_delete_evidence` | Delete an evidence |
| `core_competency_get_scale_values` | Fetch the values for a specific scale |
| `core_competency_grade_competency_in_course` | Grade a competency from the course page. |
| `core_competency_list_course_competencies` | List the competencies in a course |
| `core_competency_user_competency_plan_viewed` | Log the user competency plan viewed event. |
| `core_competency_user_competency_viewed` | Log the user competency viewed event. |
| `core_competency_user_competency_viewed_in_course` | Log the user competency viewed in course event |
| `core_competency_user_competency_viewed_in_plan` | Log the user competency viewed in plan event. |

## core_completion

| Function | Description |
|---|---|
| `core_completion_get_activities_completion_status` | Return the activities completion status for a user in a course. |
| `core_completion_get_course_completion_status` | Returns course completion status. |
| `core_completion_mark_course_self_completed` | Update the course completion status for the current user (if course self-completion is enabled). |
| `core_completion_update_activity_completion_status_manually` | Update completion status for the current user in an activity, only for activities with manual tracking. |

## core_course

| Function | Description |
|---|---|
| `core_course_check_updates` | Check if there is updates affecting the user for the given course and contexts. |
| `core_course_get_categories` | Return category details |
| `core_course_get_contents` **(planned)** | Get course contents |
| `core_course_get_course_module` | Return information about a course module |
| `core_course_get_course_module_by_instance` | Return information about a given module name and instance id |
| `core_course_get_courses` | Return course details |
| `core_course_get_courses_by_field` | Get courses matching a specific field (id/s, shortname, idnumber, category) |
| `core_course_get_enrolled_courses_by_timeline_classification` | List of enrolled courses for the given timeline classification (past, inprogress, or future). |
| `core_course_get_enrolled_courses_with_action_events_by_timeline_classification` | List of enrolled courses with action events in a given timeframe, for the given timeline classification. |
| `core_course_get_recent_courses` | List of courses a user has accessed most recently. |
| `core_course_get_updates_since` | Check if there are updates affecting the user for the given course since the given time stamp. |
| `core_course_get_user_administration_options` | Return a list of administration options in a set of courses that are avaialable or not for the current user. |
| `core_course_get_user_navigation_options` | Return a list of navigation options in a set of courses that are avaialable or not for the current user. |
| `core_course_search_courses` | Search courses by (name, module, block, tag) |
| `core_course_set_favourite_courses` | Add a list of courses to the list of favourite courses. |
| `core_course_view_course` | Log that the course was viewed |

## core_enrol

| Function | Description |
|---|---|
| `core_enrol_get_course_enrolment_methods` | Get the list of course enrolment methods |
| `core_enrol_get_enrolled_users` | Get enrolled users by course id. |
| `core_enrol_get_users_courses` **(planned)** | Get the list of courses where a user is enrolled in |
| `core_enrol_search_users` | Search within the list of course participants |

## core_files

| Function | Description |
|---|---|
| `core_files_delete_draft_files` | Delete the indicated files (or directories) from a user draft file area. |
| `core_files_get_files` | browse moodle files |
| `core_files_get_unused_draft_itemid` | Generate a new draft itemid for the current user. |

## core_filters

| Function | Description |
|---|---|
| `core_filters_get_all_states` | Retrieve all the filters and their states (including overridden ones in any context). |
| `core_filters_get_available_in_context` | Returns the filters available in the given contexts. |

## core_get

| Function | Description |
|---|---|
| `core_get_component_strings` | Return all raw strings (with {$a->xxx}), for a specific component - similar to core get_component_strings(), call |

## core_grades

| Function | Description |
|---|---|
| `core_grades_get_enrolled_users_for_search_widget` | ** DEPRECATED ** Please do not call this function any more. Use core_grades_get_enrolled_users_for_selector instead. Returns the enrolled users within and map some fields to the returned array of user objects. |
| `core_grades_get_enrolled_users_for_selector` | Returns the enrolled users within and map some fields to the returned array of user objects. |
| `core_grades_get_gradable_users` | Returns the gradable users in a course |
| `core_grades_get_gradeitems` | Get the gradeitems for a course |
| `core_grades_get_groups_for_search_widget` | ** DEPRECATED ** Please do not call this function any more. Use core_group_get_groups_for_selector instead. Get the group/(s) for a course |
| `core_grades_get_groups_for_selector` | ** DEPRECATED ** Please do not call this function any more. Use core_group_get_groups_for_selector instead. Get the group/(s) for a course |
| `core_grades_grader_gradingpanel_point_fetch` | Fetch the data required to display the grader grading panel for simple grading, creating the grade item if required |
| `core_grades_grader_gradingpanel_point_store` | Store the data required to display the grader grading panel for simple grading |
| `core_grades_grader_gradingpanel_scale_fetch` | Fetch the data required to display the grader grading panel for scale-based grading, creating the grade item if required |
| `core_grades_grader_gradingpanel_scale_store` | Store the data required to display the grader grading panel for scale-based grading |

## core_group

| Function | Description |
|---|---|
| `core_group_get_activity_allowed_groups` | Gets a list of groups that the user is allowed to access within the specified activity. |
| `core_group_get_activity_groupmode` | Returns effective groupmode used in a given activity. |
| `core_group_get_course_groupings` | Returns all groupings in specified course. |
| `core_group_get_course_groups` | Returns all groups in specified course. |
| `core_group_get_course_user_groups` | Returns all groups in specified course for the specified user. |
| `core_group_get_groups_for_selector` | Get the group/(s) for a course |

## core_h5p

| Function | Description |
|---|---|
| `core_h5p_get_trusted_h5p_file` | Get the H5P file cleaned for Mobile App. |

## core_message

| Function | Description |
|---|---|
| `core_message_block_user` | Blocks a user |
| `core_message_confirm_contact_request` | Confirms a contact request |
| `core_message_create_contact_request` | Creates a contact request |
| `core_message_data_for_messagearea_search_messages` | Retrieve the template data for searching for messages |
| `core_message_decline_contact_request` | Declines a contact request |
| `core_message_delete_contacts` | Remove contacts from the contact list |
| `core_message_delete_conversations_by_id` | Deletes a list of conversations. |
| `core_message_delete_message` | Deletes a message. |
| `core_message_delete_message_for_all_users` | Deletes a message for all users. |
| `core_message_get_blocked_users` | Retrieve a list of users blocked |
| `core_message_get_contact_requests` | Returns contact requests for a user |
| `core_message_get_conversation` | Retrieve a conversation for a user |
| `core_message_get_conversation_between_users` | Retrieve a conversation for a user between another user |
| `core_message_get_conversation_counts` | Retrieve a list of conversation counts, indexed by type. |
| `core_message_get_conversation_members` | Retrieve a list of members in a conversation |
| `core_message_get_conversation_messages` | Retrieve the conversation messages and relevant member information |
| `core_message_get_conversations` | Retrieve a list of conversations for a user |
| `core_message_get_member_info` | Retrieve a user message profiles |
| `core_message_get_messages` | Retrieve a list of messages sent and received by a user (conversations, notifications or both) |
| `core_message_get_received_contact_requests_count` | Gets the number of received contact requests |
| `core_message_get_self_conversation` | Retrieve a self-conversation for a user |
| `core_message_get_unread_conversation_counts` | Retrieve a list of unread conversation counts, indexed by type. |
| `core_message_get_unread_conversations_count` | Retrieve the count of unread conversations for a given user |
| `core_message_get_unread_notification_count` | Get number of unread notifications. |
| `core_message_get_user_contacts` | Retrieve the contact list |
| `core_message_get_user_message_preferences` | Get the message preferences for a given user. |
| `core_message_get_user_notification_preferences` | Get the notification preferences for a given user. |
| `core_message_mark_all_conversation_messages_as_read` | Mark all conversation messages as read for a given user |
| `core_message_mark_all_notifications_as_read` | Mark all notifications as read for a given user |
| `core_message_mark_message_read` | Mark a single message as read, trigger message_viewed event. |
| `core_message_mark_notification_read` | Mark a single notification as read, trigger notification_viewed event. |
| `core_message_message_processor_config_form` | Process the message processor config form |
| `core_message_message_search_users` | Retrieve the data for searching for people |
| `core_message_mute_conversations` | Mutes a list of conversations |
| `core_message_search_contacts` | Search for contacts |
| `core_message_send_instant_messages` | Send instant messages |
| `core_message_send_messages_to_conversation` | Send messages to an existing conversation between users |
| `core_message_set_favourite_conversations` | Mark a conversation or group of conversations as favourites/starred conversations. |
| `core_message_unblock_user` | Unblocks a user |
| `core_message_unmute_conversations` | Unmutes a list of conversations |
| `core_message_unset_favourite_conversations` | Unset a conversation or group of conversations as favourites/starred conversations. |

## core_my

| Function | Description |
|---|---|
| `core_my_view_page` | Trigger the My or Dashboard viewed event. |

## core_notes

| Function | Description |
|---|---|
| `core_notes_create_notes` | Create notes |
| `core_notes_delete_notes` | Delete notes |
| `core_notes_get_course_notes` | Returns all notes in specified course (or site), for the specified user. |
| `core_notes_view_notes` | Simulates the web interface view of notes/index.php: trigger events. |

## core_question

| Function | Description |
|---|---|
| `core_question_update_flag` | Update the flag state of a question attempt. |

## core_rating

| Function | Description |
|---|---|
| `core_rating_add_rating` | Rates an item. |
| `core_rating_get_item_ratings` | Retrieve all the ratings for an item. |

## core_reportbuilder

| Function | Description |
|---|---|
| `core_reportbuilder_can_view_system_report` | Determine access to a system report |
| `core_reportbuilder_list_reports` | List custom reports for current user |
| `core_reportbuilder_retrieve_report` | Retrieve custom report content |
| `core_reportbuilder_retrieve_system_report` | Retrieve system report content |
| `core_reportbuilder_view_report` | Trigger custom report viewed |

## core_search

| Function | Description |
|---|---|
| `core_search_get_results` **(planned)** | Get search results. |
| `core_search_get_search_areas_list` | Get search areas. |
| `core_search_get_top_results` | Get top search results. |
| `core_search_view_results` | Trigger view search results event. |

## core_table

| Function | Description |
|---|---|
| `core_table_get_dynamic_table_content` | Get the dynamic table content raw html |

## core_tag

| Function | Description |
|---|---|
| `core_tag_get_tag_areas` | Retrieves existing tag areas. |
| `core_tag_get_tag_cloud` | Retrieves a tag cloud for the given collection and/or query search. |
| `core_tag_get_tag_collections` | Retrieves existing tag collections. |
| `core_tag_get_tagindex` | Gets tag index page for one tag and one tag area |
| `core_tag_get_tagindex_per_area` | Gets tag index page per different areas. |

## core_user

| Function | Description |
|---|---|
| `core_user_add_user_device` | Store mobile user devices information for PUSH Notifications. |
| `core_user_add_user_private_files` | Copy files from a draft area to users private files area. |
| `core_user_agree_site_policy` | Agree the site policy for the current user. |
| `core_user_get_course_user_profiles` | Get course user profiles (each of the profils matching a course id and a user id),. |
| `core_user_get_private_files_info` | Returns general information about files in the user private files area. |
| `core_user_get_user_preferences` | Return user preferences. |
| `core_user_get_users_by_field` | Retrieve users\' information for a specified unique field - If you want to do a user search, use core_user_get_users() or core_user_search_identity(). |
| `core_user_prepare_private_files_for_edition` | Prepares the draft area for user private files. |
| `core_user_remove_user_device` | Remove a user device from the Moodle database. |
| `core_user_set_user_preferences` | Set user preferences. |
| `core_user_update_picture` | Update or delete the user picture in the site |
| `core_user_update_private_files` | Copy files from a draft area to users private files area. |
| `core_user_update_user_device_public_key` | Store mobile user public key. |
| `core_user_update_user_preferences` | Update a user\'s preferences |
| `core_user_view_user_list` | Simulates the web-interface view of user/index.php (triggering events),. |
| `core_user_view_user_profile` | Simulates the web-interface view of user/view.php and user/profile.php (triggering events),. |

## core_webservice

| Function | Description |
|---|---|
| `core_webservice_get_site_info` | Return some site info / user info / list web service functions |

## core_xapi

| Function | Description |
|---|---|
| `core_xapi_delete_state` | Delete an xAPI state data from an activityId. |
| `core_xapi_delete_states` | Delete all xAPI state data from an activityId. |
| `core_xapi_get_state` | Get an xAPI state data from an activityId. |
| `core_xapi_get_states` | Get all state ID from an activityId. |
| `core_xapi_post_state` | Post an xAPI state into an activityId. |
| `core_xapi_statement_post` | Post an xAPI statement. |

## enrol_guest

| Function | Description |
|---|---|
| `enrol_guest_get_instance_info` | Return guest enrolment instance information. |
| `enrol_guest_validate_password` | Perform password validation. |

## enrol_self

| Function | Description |
|---|---|
| `enrol_self_enrol_user` | Self enrol the current user in the given course. |
| `enrol_self_get_instance_info` | self enrolment instance information. |

## gradereport_grader

| Function | Description |
|---|---|
| `gradereport_grader_get_users_in_report` | Returns the dataset of users within the report |

## gradereport_overview

| Function | Description |
|---|---|
| `gradereport_overview_get_course_grades` | Get the given user courses final grades |
| `gradereport_overview_view_grade_report` | Trigger the report view event |

## gradereport_singleview

| Function | Description |
|---|---|
| `gradereport_singleview_get_grade_items_for_search_widget` | Get the gradeitem/(s) for a course |

## gradereport_user

| Function | Description |
|---|---|
| `gradereport_user_get_access_information` | Returns user access information for the user grade report. |
| `gradereport_user_get_grade_items` **(planned)** | Returns the complete list of grade items for users in a course |
| `gradereport_user_get_grades_table` | Get the user/s report grades table for a course |
| `gradereport_user_view_grade_report` | Trigger the report view event |

## message_airnotifier

| Function | Description |
|---|---|
| `message_airnotifier_are_notification_preferences_configured` | Check if the users have notification preferences configured yet |
| `message_airnotifier_enable_device` | Enables or disables a registered user device so it can receive Push notifications |
| `message_airnotifier_get_user_devices` | Return the list of mobile devices that are registered in Moodle for the given user |
| `message_airnotifier_is_system_configured` | Check whether the airnotifier settings have been configured |

## message_popup

| Function | Description |
|---|---|
| `message_popup_get_popup_notifications` | Retrieve a list of popup notifications for a user |
| `message_popup_get_unread_popup_notification_count` | Retrieve the count of unread popup notifications for a given user |

## mod_assign

| Function | Description |
|---|---|
| `mod_assign_get_assignments` **(planned)** | Returns the courses and assignments for the users capability |
| `mod_assign_get_grades` | Returns grades from the assignment |
| `mod_assign_get_participant` | Get a participant for an assignment, with some summary info about their submissions. |
| `mod_assign_get_submission_status` **(planned)** | Returns information about an assignment submission status for a given user. |
| `mod_assign_get_submissions` | Returns the submissions for assignments |
| `mod_assign_get_user_flags` | Returns the user flags for assignments |
| `mod_assign_get_user_mappings` | Returns the blind marking mappings for assignments |
| `mod_assign_list_participants` | List the participants for a single assignment, with some summary info about their submissions. |
| `mod_assign_lock_submissions` | Prevent students from making changes to a list of submissions |
| `mod_assign_remove_submission` | Remove submission. |
| `mod_assign_reveal_identities` | Reveal the identities for a blind marking assignment |
| `mod_assign_revert_submissions_to_draft` | Reverts the list of submissions to draft status |
| `mod_assign_save_grade` | Save a grade update for a single student. |
| `mod_assign_save_grades` | Save multiple grade updates for an assignment. |
| `mod_assign_save_submission` | Update the current students submission |
| `mod_assign_save_user_extensions` | Save a list of assignment extensions |
| `mod_assign_set_user_flags` | Creates or updates user flags |
| `mod_assign_start_submission` | Start a submission for user if assignment has a time limit. |
| `mod_assign_submit_for_grading` | Submit the current students assignment for grading |
| `mod_assign_submit_grading_form` | Submit the grading form data via ajax |
| `mod_assign_unlock_submissions` | Allow students to make changes to a list of submissions |
| `mod_assign_view_assign` | Update the module completion status. |
| `mod_assign_view_grading_table` | Trigger the grading_table_viewed event. |
| `mod_assign_view_submission_status` | Trigger the submission status viewed event. |

## mod_bigbluebuttonbn

| Function | Description |
|---|---|
| `mod_bigbluebuttonbn_can_join` | Returns information if the current user can join or not. |
| `mod_bigbluebuttonbn_completion_validate` | Validate completion |
| `mod_bigbluebuttonbn_end_meeting` | End a meeting |
| `mod_bigbluebuttonbn_get_bigbluebuttonbns_by_courses` | Returns a list of bigbluebuttonbns in a provided list of courses, if no list is provided all bigbluebuttonbns that the user can view will be returned. |
| `mod_bigbluebuttonbn_get_join_url` | Get the join URL for the meeting and create if it does not exist. |
| `mod_bigbluebuttonbn_get_recordings` | Returns a list of recordings ready to be processed by a datatable. |
| `mod_bigbluebuttonbn_get_recordings_to_import` | Returns a list of recordings ready to import to be processed by a datatable. |
| `mod_bigbluebuttonbn_meeting_info` | Get displayable information on the meeting |
| `mod_bigbluebuttonbn_update_recording` | Update a single recording |
| `mod_bigbluebuttonbn_view_bigbluebuttonbn` | Trigger the course module viewed event and update the module completion status. |

## mod_book

| Function | Description |
|---|---|
| `mod_book_get_books_by_courses` | Returns a list of book instances in a provided set of courses, if no courses are provided then all the book instances the user has access to will be returned. |
| `mod_book_view_book` | Simulate the view.php web interface book: trigger events, completion, etc... |

## mod_chat

| Function | Description |
|---|---|
| `mod_chat_get_chat_latest_messages` | Get the latest messages from the given chat session. |
| `mod_chat_get_chat_users` | Get the list of users in the given chat session. |
| `mod_chat_get_chats_by_courses` | Returns a list of chat instances in a provided set of courses, if no courses are provided then all the chat instances the user has access to will be returned. |
| `mod_chat_get_session_messages` | Retrieves messages of the given chat session. |
| `mod_chat_get_sessions` | Retrieves chat sessions for a given chat. |
| `mod_chat_login_user` | Log a user into a chat room in the given chat. |
| `mod_chat_send_chat_message` | Send a message on the given chat session. |
| `mod_chat_view_chat` | Trigger the course module viewed event and update the module completion status. |
| `mod_chat_view_sessions` | Trigger the chat session viewed event. |

## mod_checklist

| Function | Description |
|---|---|
| `mod_checklist_update_item_state` | Check or uncheck an item in a checklist for the current user. *(written by hand; plugin has no description)* |

## mod_choice

| Function | Description |
|---|---|
| `mod_choice_delete_choice_responses` | Delete the given submitted responses in a choice |
| `mod_choice_get_choice_options` | Retrieve options for a specific choice. |
| `mod_choice_get_choice_results` | Retrieve users results for a given choice. |
| `mod_choice_get_choices_by_courses` | Returns a list of choice instances in a provided set of courses, if no courses are provided then all the choice instances the user has access to will be returned. |
| `mod_choice_submit_choice_response` | Submit responses to a specific choice item. |
| `mod_choice_view_choice` | Trigger the course module viewed event and update the module completion status. |

## mod_choicegroup

| Function | Description |
|---|---|
| `mod_choicegroup_delete_choicegroup_responses` | Delete the given submitted responses in a choice group |
| `mod_choicegroup_get_choicegroup_options` | Retrieve options for a specific choicegroup. |
| `mod_choicegroup_submit_choicegroup_response` | Submit responses to a specific choicegroup item. |
| `mod_choicegroup_view_choicegroup` | Trigger the course module viewed event and update the module completion status. |

## mod_data

| Function | Description |
|---|---|
| `mod_data_add_entry` | Adds a new entry. |
| `mod_data_approve_entry` | Approves or unapproves an entry. |
| `mod_data_delete_entry` | Deletes an entry. |
| `mod_data_get_data_access_information` | Return access information for a given database. |
| `mod_data_get_databases_by_courses` | Returns a list of database instances in a provided set of courses, if no courses are provided then all the database instances the user has access to will be returned. |
| `mod_data_get_entries` | Return the complete list of entries of the given database. |
| `mod_data_get_entry` | Return one entry record from the database, including contents optionally. |
| `mod_data_get_fields` | Return the list of configured fields for the given database. |
| `mod_data_search_entries` | Search for entries in the given database. |
| `mod_data_update_entry` | Updates an existing entry. |
| `mod_data_view_database` | Simulate the view.php web interface data: trigger events, completion, etc... |

## mod_feedback

| Function | Description |
|---|---|
| `mod_feedback_get_analysis` | Retrieves the feedback analysis. |
| `mod_feedback_get_current_completed_tmp` | Returns the temporary completion record for the current user. |
| `mod_feedback_get_feedback_access_information` | Return access information for a given feedback. |
| `mod_feedback_get_feedbacks_by_courses` | Returns a list of feedbacks in a provided list of courses, if no list is provided all feedbacks that the user can view will be returned. |
| `mod_feedback_get_finished_responses` | Retrieves responses from the last finished attempt. |
| `mod_feedback_get_items` | Returns the items (questions) in the given feedback. |
| `mod_feedback_get_last_completed` | Retrieves the last completion record for the current user. |
| `mod_feedback_get_non_respondents` | Retrieves a list of students who didn\'t submit the feedback. |
| `mod_feedback_get_page_items` | Get a single feedback page items. |
| `mod_feedback_get_responses_analysis` | Return the feedback user responses analysis. |
| `mod_feedback_get_unfinished_responses` | Retrieves responses from the current unfinished attempt. |
| `mod_feedback_launch_feedback` | Starts or continues a feedback submission. |
| `mod_feedback_process_page` | Process a jump between pages. |
| `mod_feedback_view_feedback` | Trigger the course module viewed event and update the module completion status. |

## mod_folder

| Function | Description |
|---|---|
| `mod_folder_get_folders_by_courses` | Returns a list of folders in a provided list of courses, if no list is provided all folders that the user can view will be returned. Please note that this WS is not returning the folder contents. |
| `mod_folder_view_folder` | Simulate the view.php web interface folder: trigger events, completion, etc... |

## mod_forum

| Function | Description |
|---|---|
| `mod_forum_add_discussion` | Add a new discussion into an existing forum. |
| `mod_forum_add_discussion_post` | Create new posts into an existing discussion. |
| `mod_forum_can_add_discussion` | Check if the current user can add discussions in the given forum (and optionally for the given group). |
| `mod_forum_delete_post` | Deletes a post or a discussion completely when the post is the discussion topic. |
| `mod_forum_get_discussion_post` | Get a particular discussion post. |
| `mod_forum_get_discussion_posts` **(planned)** | Returns a list of forum posts for a discussion. |
| `mod_forum_get_forum_access_information` | Return capabilities information for a given forum. |
| `mod_forum_get_forum_discussions` **(planned)** | Returns a list of forum discussions optionally sorted and paginated. |
| `mod_forum_get_forums_by_courses` | Returns a list of forum instances in a provided set of courses, if no courses are provided then all the forum instances the user has access to will be returned. |
| `mod_forum_prepare_draft_area_for_post` | Prepares a draft area for editing a post. |
| `mod_forum_set_lock_state` | Set the lock state for the discussion |
| `mod_forum_set_pin_state` | Set the pin state |
| `mod_forum_set_subscription_state` | Set the subscription state |
| `mod_forum_toggle_favourite_state` | Toggle the favourite state |
| `mod_forum_update_discussion_post` | Updates a post or a discussion topic post. |
| `mod_forum_view_forum` | Trigger the course module viewed event and update the module completion status. |
| `mod_forum_view_forum_discussion` | Trigger the forum discussion viewed event. |

## mod_glossary

| Function | Description |
|---|---|
| `mod_glossary_add_entry` | Add a new entry to a given glossary |
| `mod_glossary_delete_entry` | Delete the given entry from the glossary. |
| `mod_glossary_get_authors` | Get the authors. |
| `mod_glossary_get_categories` | Get the categories. |
| `mod_glossary_get_entries_by_author` | Browse entries by author. |
| `mod_glossary_get_entries_by_author_id` | Browse entries by author ID. |
| `mod_glossary_get_entries_by_category` | Browse entries by category. |
| `mod_glossary_get_entries_by_date` | Browse entries by date. |
| `mod_glossary_get_entries_by_letter` | Browse entries by letter. |
| `mod_glossary_get_entries_by_search` | Browse entries by search query. |
| `mod_glossary_get_entries_by_term` | Browse entries by term (concept or alias). |
| `mod_glossary_get_entries_to_approve` | Browse entries to be approved. |
| `mod_glossary_get_entry_by_id` | Get an entry by ID |
| `mod_glossary_get_glossaries_by_courses` | Retrieve a list of glossaries from several courses. |
| `mod_glossary_prepare_entry_for_edition` | Prepares the given entry for edition returning draft item areas and file areas information. |
| `mod_glossary_update_entry` | Updates the given glossary entry. |
| `mod_glossary_view_entry` | Notify a glossary entry as being viewed. |
| `mod_glossary_view_glossary` | Notify the glossary as being viewed. |

## mod_h5pactivity

| Function | Description |
|---|---|
| `mod_h5pactivity_get_attempts` | Return the information needed to list a user attempts. |
| `mod_h5pactivity_get_h5pactivities_by_courses` | Returns a list of h5p activities in a list of provided courses, if no list is provided all h5p activities that the user can view will be returned. |
| `mod_h5pactivity_get_h5pactivity_access_information` | Return access information for a given h5p activity. |
| `mod_h5pactivity_get_results` | Return the information needed to list a user attempt results. |
| `mod_h5pactivity_get_user_attempts` | Return the information needed to list all enrolled user attempts. |
| `mod_h5pactivity_log_report_viewed` | Log that the h5pactivity was viewed. |
| `mod_h5pactivity_view_h5pactivity` | Trigger the course module viewed event and update the module completion status. |

## mod_imscp

| Function | Description |
|---|---|
| `mod_imscp_get_imscps_by_courses` | Returns a list of IMSCP instances in a provided set of courses, if no courses are provided then all the IMSCP instances the user has access to will be returned. |
| `mod_imscp_view_imscp` | Simulate the view.php web interface imscp: trigger events, completion, etc... |

## mod_label

| Function | Description |
|---|---|
| `mod_label_get_labels_by_courses` | Returns a list of labels in a provided list of courses, if no list is provided all labels that the user can view will be returned. |

## mod_lesson

| Function | Description |
|---|---|
| `mod_lesson_finish_attempt` | Finishes the current attempt. |
| `mod_lesson_get_attempts_overview` | Get a list of all the attempts made by users in a lesson. |
| `mod_lesson_get_content_pages_viewed` | Return the list of content pages viewed by a user during a lesson attempt. |
| `mod_lesson_get_lesson` | Return information of a given lesson. |
| `mod_lesson_get_lesson_access_information` | Return access information for a given lesson. |
| `mod_lesson_get_lessons_by_courses` | Returns a list of lessons in a provided list of courses, if no list is provided all lessons that the user can view will be returned. |
| `mod_lesson_get_page_data` | Return information of a given page, including its contents. |
| `mod_lesson_get_pages` | Return the list of pages in a lesson (based on the user permissions). |
| `mod_lesson_get_pages_possible_jumps` | Return all the possible jumps for the pages in a given lesson. |
| `mod_lesson_get_questions_attempts` | Return the list of questions attempts in a given lesson. |
| `mod_lesson_get_user_attempt` | Return information about the given user attempt (including answers). |
| `mod_lesson_get_user_attempt_grade` | Return grade information in the attempt for a given user. |
| `mod_lesson_get_user_grade` | Return the final grade in the lesson for the given user. |
| `mod_lesson_get_user_timers` | Return the timers in the current lesson for the given user. |
| `mod_lesson_launch_attempt` | Starts a new attempt or continues an existing one. |
| `mod_lesson_process_page` | Processes page responses. |
| `mod_lesson_view_lesson` | Trigger the course module viewed event and update the module completion status. |

## mod_lti

| Function | Description |
|---|---|
| `mod_lti_get_ltis_by_courses` | Returns a list of external tool instances in a provided set of courses, if no courses are provided then all the external tool instances the user has access to will be returned. |
| `mod_lti_get_tool_launch_data` | Return the launch data for a given external tool. |
| `mod_lti_view_lti` | Trigger the course module viewed event and update the module completion status. |

## mod_page

| Function | Description |
|---|---|
| `mod_page_get_pages_by_courses` **(planned)** | Returns a list of pages in a provided list of courses, if no list is provided all pages that the user can view will be returned. |
| `mod_page_view_page` | Simulate the view.php web interface page: trigger events, completion, etc... |

## mod_questionnaire

| Function | Description |
|---|---|
| `mod_questionnaire_submit_questionnaire_response` | Questionnaire submit |

## mod_quiz

| Function | Description |
|---|---|
| `mod_quiz_get_attempt_access_information` | Return access information for a given attempt in a quiz. |
| `mod_quiz_get_attempt_data` | Returns information for the given attempt page for a quiz attempt in progress. |
| `mod_quiz_get_attempt_review` | Returns review information for the given finished attempt, can be used by users or teachers. |
| `mod_quiz_get_attempt_summary` | Returns a summary of a quiz attempt before it is submitted. |
| `mod_quiz_get_combined_review_options` | Combines the review options from a number of different quiz attempts. |
| `mod_quiz_get_quiz_access_information` | Return access information for a given quiz. |
| `mod_quiz_get_quiz_feedback_for_grade` | Get the feedback text that should be show to a student who got the given grade in the given quiz. |
| `mod_quiz_get_quiz_required_qtypes` | Return the potential question types that would be required for a given quiz. |
| `mod_quiz_get_quizzes_by_courses` | Returns a list of quizzes in a provided list of courses, if no list is provided all quizzes that the user can view will be returned. |
| `mod_quiz_get_user_attempts` | Return a list of attempts for the given quiz and user. |
| `mod_quiz_get_user_best_grade` | Get the best current grade for the given user on a quiz. |
| `mod_quiz_process_attempt` | Process responses during an attempt at a quiz and also deals with attempts finishing. |
| `mod_quiz_save_attempt` | Processes save requests during the quiz. This function is intended for the quiz auto-save feature. |
| `mod_quiz_start_attempt` | Starts a new attempt at a quiz. |
| `mod_quiz_view_attempt` | Trigger the attempt viewed event. |
| `mod_quiz_view_attempt_review` | Trigger the attempt reviewed event. |
| `mod_quiz_view_attempt_summary` | Trigger the attempt summary viewed event. |
| `mod_quiz_view_quiz` | Trigger the course module viewed event and update the module completion status. |

## mod_resource

| Function | Description |
|---|---|
| `mod_resource_get_resources_by_courses` | Returns a list of files in a provided list of courses, if no list is provided all files that the user can view will be returned. |
| `mod_resource_view_resource` | Simulate the view.php web interface resource: trigger events, completion, etc... |

## mod_scorm

| Function | Description |
|---|---|
| `mod_scorm_get_scorm_access_information` | Return capabilities information for a given scorm. |
| `mod_scorm_get_scorm_attempt_count` | Return the number of attempts done by a user in the given SCORM. |
| `mod_scorm_get_scorm_sco_tracks` | Retrieves SCO tracking data for the given user id and attempt number |
| `mod_scorm_get_scorm_scoes` | Returns a list containing all the scoes data related to the given scorm id |
| `mod_scorm_get_scorm_user_data` | Retrieves user tracking and SCO data and default SCORM values |
| `mod_scorm_get_scorms_by_courses` | Returns a list of scorm instances in a provided set of courses, if no courses are provided then all the scorm instances the user has access to will be returned. |
| `mod_scorm_insert_scorm_tracks` | Saves a scorm tracking record. It will overwrite any existing tracking data for this attempt. Validation should be performed before running the function to ensure the user will not lose any existing attempt data. |
| `mod_scorm_launch_sco` | Trigger the SCO launched event. |
| `mod_scorm_view_scorm` | Trigger the course module viewed event. |

## mod_survey

| Function | Description |
|---|---|
| `mod_survey_get_questions` | Get the complete list of questions for the survey, including subquestions. |
| `mod_survey_get_surveys_by_courses` | Returns a list of survey instances in a provided set of courses, if no courses are provided then all the survey instances the user has access to will be returned. |
| `mod_survey_submit_answers` | Submit the answers for a given survey. |
| `mod_survey_view_survey` | Trigger the course module viewed event and update the module completion status. |

## mod_url

| Function | Description |
|---|---|
| `mod_url_get_urls_by_courses` | Returns a list of urls in a provided list of courses, if no list is provided all urls that the user can view will be returned. |
| `mod_url_view_url` | Trigger the course module viewed event and update the module completion status. |

## mod_wiki

| Function | Description |
|---|---|
| `mod_wiki_edit_page` | Save the contents of a page. |
| `mod_wiki_get_page_contents` | Returns the contents of a page. |
| `mod_wiki_get_page_for_editing` | Locks and retrieves info of page-section to be edited. |
| `mod_wiki_get_subwiki_files` | Returns the list of files for a specific subwiki. |
| `mod_wiki_get_subwiki_pages` | Returns the list of pages for a specific subwiki. |
| `mod_wiki_get_subwikis` | Returns the list of subwikis the user can see in a specific wiki. |
| `mod_wiki_get_wikis_by_courses` | Returns a list of wiki instances in a provided set of courses, if no courses are provided then all the wiki instances the user has access to will be returned. |
| `mod_wiki_new_page` | Create a new page in a subwiki. |
| `mod_wiki_view_page` | Trigger the page viewed event and update the module completion status. |
| `mod_wiki_view_wiki` | Trigger the course module viewed event and update the module completion status. |

## mod_workshop

| Function | Description |
|---|---|
| `mod_workshop_add_submission` | Add a new submission to a given workshop. |
| `mod_workshop_delete_submission` | Deletes the given submission. |
| `mod_workshop_evaluate_assessment` | Evaluates an assessment (used by teachers for provide feedback to the reviewer). |
| `mod_workshop_evaluate_submission` | Evaluates a submission (used by teachers for provide feedback or override the submission grade). |
| `mod_workshop_get_assessment` | Retrieves the given assessment. |
| `mod_workshop_get_assessment_form_definition` | Retrieves the assessment form definition. |
| `mod_workshop_get_grades` | Returns the assessment and submission grade for the given user. |
| `mod_workshop_get_grades_report` | Retrieves the assessment grades report. |
| `mod_workshop_get_reviewer_assessments` | Retrieves all the assessments reviewed by the given user. |
| `mod_workshop_get_submission` | Retrieves the given submission. |
| `mod_workshop_get_submission_assessments` | Retrieves all the assessments of the given submission. |
| `mod_workshop_get_submissions` | Retrieves all the workshop submissions or the one done by the given user (except example submissions). |
| `mod_workshop_get_user_plan` | Return the planner information for the given user. |
| `mod_workshop_get_workshop_access_information` | Return access information for a given workshop. |
| `mod_workshop_get_workshops_by_courses` | Returns a list of workshops in a provided list of courses, if no list is provided all workshops that the user can view will be returned. |
| `mod_workshop_update_assessment` | Add information to an allocated assessment. |
| `mod_workshop_update_submission` | Update the given submission. |
| `mod_workshop_view_submission` | Trigger the submission viewed event. |
| `mod_workshop_view_workshop` | Trigger the course module viewed event and update the module completion status. |

## report_insights

| Function | Description |
|---|---|
| `report_insights_action_executed` | Stores an action executed over a group of predictions. |
| `report_insights_set_fixed_prediction` | Flags a prediction as fixed. |
| `report_insights_set_notuseful_prediction` | Flags the prediction as not useful. |

## tool_analytics

| Function | Description |
|---|---|
| `tool_analytics_potential_contexts` | Retrieve the list of potential contexts for a model. |

## tool_dataprivacy

| Function | Description |
|---|---|
| `tool_dataprivacy_cancel_data_request` | Cancel the data request made by the user |
| `tool_dataprivacy_contact_dpo` | Contact the site Data Protection Officer(s) |
| `tool_dataprivacy_create_data_request` | Creates a data request. |
| `tool_dataprivacy_get_access_information` | Retrieving privacy API access (permissions) information for the current user. |
| `tool_dataprivacy_get_data_requests` | Gets data request. |

## tool_lp

| Function | Description |
|---|---|
| `tool_lp_data_for_course_competencies_page` | Load the data for the course competencies page template. |
| `tool_lp_data_for_plan_page` | Load the data for the plan page template. |
| `tool_lp_data_for_plans_page` | Load the data for the plans page template |
| `tool_lp_data_for_user_competency_summary` | Load a summary of a user competency. |
| `tool_lp_data_for_user_competency_summary_in_course` | Load a summary of a user competency. |
| `tool_lp_data_for_user_competency_summary_in_plan` | Load a summary of a user competency. |
| `tool_lp_data_for_user_evidence_list_page` | Load the data for the user evidence list page template |
| `tool_lp_data_for_user_evidence_page` | Load the data for the user evidence page template |

## tool_mobile

| Function | Description |
|---|---|
| `tool_mobile_call_external_functions` | Call multiple external functions and return all responses. |
| `tool_mobile_get_autologin_key` | Creates an auto-login key for the current user. Is created only in https sites and is restricted by time, ip address and only works if the request comes from the Moodle mobile or desktop app. |
| `tool_mobile_get_config` | Returns a list of the site configurations, filtering by section. |
| `tool_mobile_get_content` | Returns a piece of content to be displayed in the Mobile app. |
| `tool_mobile_get_plugins_supporting_mobile` | Returns a list of Moodle plugins supporting the mobile app. |
| `tool_mobile_get_public_config` | Returns a list of the site public settings, those not requiring authentication. |
| `tool_mobile_get_tokens_for_qr_login` | Returns a WebService token (and private token) for QR login. |
| `tool_mobile_validate_subscription_key` | Check if the given site subscription key is valid. |

## tool_moodlenet

| Function | Description |
|---|---|
| `tool_moodlenet_search_courses` | For some given input search for a course that matches |
| `tool_moodlenet_verify_webfinger` | Verify if the passed information resolves into a WebFinger profile URL |

## tool_policy

| Function | Description |
|---|---|
| `tool_policy_get_user_acceptances` | Get user policies acceptances. |
| `tool_policy_set_acceptances_status` | Set the acceptance status (accept or decline only) for the indicated policies for the given user. |
